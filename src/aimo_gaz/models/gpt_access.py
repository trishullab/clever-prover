#!/usr/bin/env python3

import sys
root_dir = __file__.split('src')[0]
if root_dir not in sys.path:
    sys.path.append(root_dir)
import os
import json
from openai import OpenAI
import typing

class GptAccess(object):

    def __init__(self,
        secret_filepath: str = ".secrets/openai_key.json",
        model_name: typing.Optional[str] = None) -> None:
        assert secret_filepath.endswith(".json"), "Secret filepath must be a .json file"
        assert os.path.exists(secret_filepath), "Secret filepath does not exist"
        self.secret_filepath = secret_filepath
        api_key = self._get_secret()
        self.client = OpenAI(api_key=api_key)
        self.models_supported = self.client.models.list().data
        self.models_supported_name = [model.id for model in self.models_supported]
        if model_name is not None:
            assert model_name in self.models_supported_name, f"Model name {model_name} not supported"
            self.model_name = model_name
        self.is_open_ai_model = True
        self.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    def complete_chat(self,
            messages: typing.List[typing.Dict[str, str]],
            model: typing.Optional[str] = None,
            n: int = 1,
            max_tokens: int = 5,
            temperature: float = 0.25,
            top_p: float = 1.0,
            frequency_penalty: float = 0.0,
            presence_penalty: float = 0.0,
            stop: list = []) -> typing.Tuple[list, dict]:
        model = self.model_name if model is None else model
        if self.is_open_ai_model:
            if self.model_name == "o1-mini" or self.model_name == "o3-mini": # TODO: find a less hacky way to do this
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens*3, # TODO: find a less hacky way to do this (that prints the right token size)
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop=stop,
                    n=n
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop=stop,
                    n=n
                )
            usage = response.usage
            self.usage["prompt_tokens"] += usage.prompt_tokens
            self.usage["completion_tokens"] += usage.completion_tokens
            self.usage["total_tokens"] += usage.total_tokens
        else:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                # top_p=top_p,
                stop=stop,
                n=n
            )
            usage = response.usage
            self.usage["prompt_tokens"] += usage.prompt_tokens
            self.usage["completion_tokens"] += usage.completion_tokens
            self.usage["total_tokens"] += usage.total_tokens
        return_responses = [{"role": choice.message.role, "content": choice.message.content} for choice in response.choices]
        for i in range(len(return_responses) - 1):
            return_responses[i]["finish_reason"] = "stop"
        if len(response.choices) > 0:
            return_responses[-1]["finish_reason"] = response.choices[-1].finish_reason
        usage_dict = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "reason": response.choices[-1].finish_reason if len(response.choices) > 0 else "stop"
        }
        return return_responses, usage_dict

    def _get_secret(self) -> str:
        with open(self.secret_filepath, "r") as f:
            secret = json.load(f)
            # openai.organization = secret["organization"]
            api_key = secret["api_key"]
        return api_key

if __name__ == "__main__":
    os.chdir(root_dir)
    # openai_access = GptAccess(model_name="gpt-3.5-turbo")
    openai_access = GptAccess(model_name="gpt-4")
    # openai_access = GptAccess(model_name="davinci")
    messages = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Things working well together will increase revenue.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Let's talk later when we're less busy about how to do better.",
        },
        {
            "role": "user",
            "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
        },
        {
            "role": "user",
            "content": "Our idea seems to be scooped, don't know how to change direction now."
        }
    ]
    print(openai_access.complete_chat(messages, max_tokens=15, n=2, temperature=0.8))
