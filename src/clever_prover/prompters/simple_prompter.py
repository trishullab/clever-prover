#!/usr/bin/env python3

import typing
import os
import time
import logging
from copra.agent.rate_limiter import RateLimiter
from copra.gpts.gpt_access import GptAccess
from copra.gpts.llama_access import LlamaAccess, ServiceDownError
from copra.prompt_generator.dfs_agent_grammar import DfsAgentGrammar
from copra.tools.misc import model_supports_openai_api

class SimplePrompter:
    def __init__(self, 
            main_sys_prompt_path: str, 
            example_conv_prompt_path: str,
            num_sequences: int = 1,
            temperature: float = 0.25,
            max_tokens_per_action: int = 50,
            max_history_messages: int = 0, # This means keep no history of messages
            model_name: str = "gpt-3.5-turbo",
            secret_filepath: str = ".secrets/openai_key.json",
            end_tokens: typing.List[str] = ["[END]"],
            k : typing.Optional[int] = None,
            logger: logging.Logger = None,
            model_params: typing.Optional[typing.Dict[str, typing.Any]] = None):
        assert os.path.exists(main_sys_prompt_path), f"{main_sys_prompt_path} doesn't exists"
        assert os.path.exists(example_conv_prompt_path), f"{example_conv_prompt_path} doesn't exists"
        self.agent_grammar = DfsAgentGrammar(user_name="example_user", agent_name="example_assistant")
        self.model_name = model_name
        conv_messages = self.agent_grammar.get_openai_conv_messages(example_conv_prompt_path, "system")
        main_message = self.agent_grammar.get_openai_main_message(main_sys_prompt_path, "system")
        self.system_messages = [main_message] + conv_messages
        if not model_supports_openai_api(model_name):
            self._gpt_access = LlamaAccess(model_name)
        else:
            self._gpt_access = GptAccess(secret_filepath=secret_filepath, model_name=model_name)
        self._token_limit_per_min = GptAccess.gpt_model_info[model_name]["token_limit_per_min"]
        self._request_limit_per_min = GptAccess.gpt_model_info[model_name]["request_limit_per_min"]
        self._max_token_per_prompt = GptAccess.gpt_model_info[model_name]["max_token_per_prompt"]
        self._rate_limiter = RateLimiter(self._token_limit_per_min, self._request_limit_per_min)
        self.temperature = temperature
        self.num_sequences = num_sequences
        self.system_token_count = self._gpt_access.num_tokens_from_messages(self.system_messages)
        self._model_params = model_params if model_params is not None else {}
        self._max_tokens_per_action = max_tokens_per_action
        self._history_token_count = 0
        self._message_history = []
        self._message_history_token_count = []
        self._custom_system_messages = []
        self._max_history_messages = max_history_messages
        self._k = k
        self.logger : logging.Logger = logger if logger is not None else logging.getLogger(__name__)
        self._num_api_calls = 0
        self._end_tokens = end_tokens
        pass

    def __enter__(self):
        if isinstance(self._gpt_access, LlamaAccess):
            self._gpt_access.__enter__()
    
    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(self._gpt_access, LlamaAccess):
            self._gpt_access.__exit__(exc_type, exc_value, traceback)

    def add_to_history(self, message: typing.Any):
        message_token_count = self._gpt_access.num_tokens_from_messages([message])
        self._message_history.append(message)
        self._message_history_token_count.append(message_token_count)
        self._history_token_count += message_token_count
    
    def reset_last_message(self, message: typing.Any):
        if len(self._message_history) > 0:
            self._history_token_count -= self._message_history_token_count[-1]
            self._message_history.pop()
            self._message_history_token_count.pop()
        self.add_to_history(message)

    def _constrain_tokens_in_history(self, prompt_message, prompt_token_count: int, max_tokens_per_action: int) -> list:
        if len(self._message_history) >= self._max_history_messages:
            history_idx = len(self._message_history) - self._max_history_messages
        else:
            history_idx = 0
        if history_idx < len(self._message_history):
            # There is no point in checking the token count if there is no history to be maintained
            total_token_count = self.system_token_count + self._history_token_count + prompt_token_count
            max_token_per_prompt = min(self._max_token_per_prompt, self._max_token_per_prompt - max_tokens_per_action)
            assert max_token_per_prompt > 0, "Max token per prompt must be greater than 0, please decrease max_tokens_per_action"
            tokens_shredded = False
            remove_cnt  = 0
            history_count = self._history_token_count
            while total_token_count >= max_token_per_prompt and history_idx < len(self._message_history):
                self.logger.warning(f"Tokens exceeded removing history at index {history_idx}: {total_token_count} >= {max_token_per_prompt}")
                history_count -= self._message_history_token_count[history_idx]
                total_token_count = self.system_token_count + history_count + prompt_token_count
                history_idx += 1
                tokens_shredded = True
                remove_cnt += 1
            if remove_cnt % 2 == 1 and history_idx < len(self._message_history):
                history_count -= self._message_history_token_count[history_idx]
                total_token_count = self.system_token_count + history_count + prompt_token_count
                history_idx += 1
            if tokens_shredded:
                self.logger.warning(f"Shredded tokens from history. New total token count: {total_token_count}, max token per prompt: {max_token_per_prompt}, history token count: {self._history_token_count}, prompt token count: {prompt_token_count}")
            if total_token_count >= max_token_per_prompt:
                self.logger.warning(f"Total token count {total_token_count} is still greater than max token per prompt {max_token_per_prompt}.")
        else:
            total_token_count = self.system_token_count + prompt_token_count
        if history_idx > 0:
            for idx in range(min(history_idx, len(self._message_history))):
                self._history_token_count -= self._message_history_token_count[idx]
        self._message_history = self._message_history[history_idx:]
        self._message_history_token_count = self._message_history_token_count[history_idx:]
        self._message_history.append(prompt_message)
        self._message_history_token_count.append(prompt_token_count)
        self._history_token_count += prompt_token_count
        messages = self.system_messages + self._custom_system_messages + self._message_history
        assert total_token_count + max_tokens_per_action <= self._max_token_per_prompt, f"Total token count {total_token_count} + max tokens per action {max_tokens_per_action} is greater than max token per prompt {self._max_token_per_prompt}"
        return messages, total_token_count
    
    def _throttle_if_needed(self, total_token_count: int):
        has_hit_rate_limit = self._rate_limiter.check(total_token_count)
        was_throttled = False
        while not has_hit_rate_limit:
            current_time = time.time()
            time_to_sleep = max(1, 60 - (current_time - self._rate_limiter._last_request_time))
            self.logger.info(f"Rate limit reached. Sleeping for {time_to_sleep} seconds. "
            f"Rate limiter info: {self._rate_limiter}")
            time.sleep(time_to_sleep)
            has_hit_rate_limit = self._rate_limiter.check(total_token_count)
            was_throttled = True
        if was_throttled:
            self.logger.info("Rate limit was hit. So the request was throttled.")
            self._rate_limiter.reset()
            self.logger.info("Rate limit reset now.")

    def _get_prompt_message(self, message: str, max_tokens_in_prompt: int) -> str:
        assert max_tokens_in_prompt > 0, "Max token per prompt must be greater than 0, please decrease max_tokens_per_action"
        characters_per_token = 4.0
        full_prompt_message = message
        prompt_char_cnt = len(full_prompt_message)
        full_prompt_message = self.agent_grammar.get_openai_main_message_from_string(full_prompt_message, "user")
        prompt_token_count = self._gpt_access.num_tokens_from_messages([full_prompt_message])
        characters_per_token = prompt_char_cnt / prompt_token_count
        decrement_factor = 0.1
        characters_per_token -= decrement_factor
        retries = 50
        prompt_message = full_prompt_message
        prompt_messages = [full_prompt_message]
        assert (characters_per_token < 0 and prompt_token_count > max_tokens_in_prompt) or characters_per_token > 0, f"Characters per token is {characters_per_token} for {prompt_char_cnt} characters and {prompt_token_count} tokens, and max token for problem is {max_token_for_problem}"
        while prompt_token_count > max_tokens_in_prompt and retries > 0 and characters_per_token > 0:
            max_chars_in_prompt = int(max_tokens_in_prompt * characters_per_token)
            prompt_message = message[:max_chars_in_prompt]
            prompt_char_cnt = len(prompt_message)
            prompt_message = self.agent_grammar.get_openai_main_message_from_string(prompt_message, "user")
            prompt_messages = [prompt_message]
            prompt_token_count = self._gpt_access.num_tokens_from_messages(prompt_messages)
            retries -= 1
            characters_per_token -= decrement_factor
            if prompt_token_count > max_tokens_in_prompt:
                self.logger.warning(f"Prompt token count {prompt_token_count} is greater than max token per prompt {max_tokens_in_prompt}. Retrying with {characters_per_token} characters per token.")
            assert prompt_char_cnt > 0, f"Prompt message is empty. Please decrease max_tokens_per_action. Current value: {self._max_tokens_per_action}"

        prompt_token_count = self._gpt_access.num_tokens_from_messages(prompt_messages)
        assert prompt_token_count <= max_tokens_in_prompt, f"Prompt token count {prompt_token_count} is greater than max token per prompt {max_tokens_in_prompt}"
        return prompt_message, prompt_token_count

    def run_prompt(self, message: str) -> list:
        max_tokens_in_prompt = self._max_token_per_prompt - self.system_token_count - self._max_tokens_per_action
        prompt_message, prompt_token_count = self._get_prompt_message(message, max_tokens_in_prompt)
        prompt_token_count = self._gpt_access.num_tokens_from_messages([prompt_message])
        messages, total_token_count = self._constrain_tokens_in_history(prompt_message, prompt_token_count, self._max_tokens_per_action)
        success = False
        retries = 6
        time_to_sleep = 60
        exp_factor = 1.06
        tokens_factor = 1.75
        temp_factor = 0.025
        max_temp = 0.4
        temperature = self.temperature
        tokens_to_generate = self._max_tokens_per_action
        upper_bound = 10 * self._max_tokens_per_action
        responses = None
        while not success and retries > 0:
            try:
                self._throttle_if_needed(total_token_count)
                self.logger.info(f"Requesting {tokens_to_generate} tokens to generate, {total_token_count} tokens in input.")
                self.logger.info(f"Prompt Message:\n{prompt_message['content']}")
                request_start_time = time.time()
                if len(self._model_params) > 0:
                    responses, usage = self._gpt_access.complete_chat(
                        messages,
                        n=self.num_sequences,
                        temperature=temperature,
                        max_tokens=tokens_to_generate,
                        stop=self._end_tokens,
                        **self._model_params)
                else:
                    responses, usage = self._gpt_access.complete_chat(
                        messages,
                        n=self.num_sequences,
                        temperature=temperature,
                        max_tokens=tokens_to_generate,
                        stop=self._end_tokens)
                request_end_time = time.time()
                time_taken = request_end_time - request_start_time
                apporx_output_tokens = usage["total_tokens"] - total_token_count
                self.logger.info(f"Request took {time_taken} seconds. Used {usage['total_tokens']} tokens. Used {usage['completion_tokens']} completion tokens. Approx. output {apporx_output_tokens} tokens.")
                reason = usage["reason"]
                self._rate_limiter.update(usage["total_tokens"], request_start_time, request_end_time)
                success = reason != "length" or tokens_to_generate >= upper_bound
                if not success:
                    tokens_to_generate = min(int(tokens_to_generate * tokens_factor), upper_bound)
                    self.logger.info(f"Retrying with {tokens_to_generate} tokens. Earlier response was not complete for reason: {reason}.  Used {usage['completion_tokens']} completion tokens.")
                    self.logger.info(f"Incomplete Response messages: \n{responses}")
                    max_token_per_prompt = self._max_token_per_prompt - self.system_token_count - tokens_to_generate
                    prompt_message, prompt_token_count = self._get_prompt_message(message, max_token_per_prompt) # Re-generate the prompt message within new token limit
                    messages, total_token_count = self._constrain_tokens_in_history(prompt_message, prompt_token_count, tokens_to_generate)
                    # temperature = max(max_temp, temperature + temp_factor)
                    # don't change temperature for now
                else:
                    if tokens_to_generate >= upper_bound:
                        self.logger.warning(f"Retried {retries} times but still got an incomplete response. Reason: {reason}.")
                        self.logger.info(f"Maxed out response: \n{responses}")
                    else:
                        self.logger.debug(f"Got a valid response. Reason: \n{reason}")
                        self.logger.debug(f"Response messages: \n{responses}")
                self._num_api_calls += 1
            except ServiceDownError as e:
                self.logger.info("Got a service down error. Will giveup until the docker container is restarted.")
                self.logger.exception(e)
                raise
            except Exception as e:
                self.logger.info("Got an unknown exception. Retrying.")
                self.logger.exception(e)
                time.sleep(time_to_sleep)
                responses = []
                usage = {}
                time_to_sleep *= exp_factor # Exponential backoff
            retries -= 1
        if not success and responses == None:
            # Don't throw an error even with an incomplete response, because the parsing can still make it work.
            raise Exception(f"Failed to get valid response after {retries} tries")
        return responses


    def get_efficiency_info(self) -> typing.Dict[str, typing.Any]:
        return {
            "api_calls": self._num_api_calls
        }