import typing
import copy
from clever_prover.models.abs_model import GenerationResult, GenerationResults, Model
from clever_prover.models.gpt_access import GptAccess
import logging

class GptModel(Model):
    def __init__(self, name: str, logger: logging.Logger = None, *, secret_filepath: str = "../../.secrets/openai_key.json"):
        self._gpt_access = GptAccess(secret_filepath, model_name=name)
        self.logger = logger
    
    def is_loaded(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def run_prompt(self, text: typing.List[typing.Dict[str, str]], **kwargs) -> list:
        success = False
        retries = 3
        tokens_factor = 1.75
        generated_text = None
        while not success and retries > 0:
            generated_text, usage = self._gpt_access.complete_chat(text, **kwargs)
            reason = usage["reason"]
            success = (reason != "length")
            if not success:
                old_max_tokens = kwargs["max_tokens"]
                kwargs["max_tokens"] = int(kwargs["max_tokens"] * tokens_factor)
                self.logger.info(f"Response cut off at {old_max_tokens} tokens. Retrying with {kwargs['max_tokens']} tokens.") # TODO: print something different when not retrying
                self.logger.info(f"Incomplete response:\n{generated_text}")
            else:
                self.logger.info(f"Got a valid response. Reason: {reason}")
            retries -= 1
        return generated_text

    def generate(self,
                 inputs: typing.Union[typing.List[typing.List[typing.Dict[str, str]]], typing.List[typing.Dict[str, str]]],
                 **kwargs
                 ) -> GenerationResults:

        expected_kwargs = set(["n", "max_tokens", "temperature", "top_p", "frequency_penalty", "presence_penalty", "stop"])
        for arg in kwargs:
            assert arg in expected_kwargs, \
                f"""Unexpected argument '{arg}' found in kwargs passed to generate()

All passed kwargs: {kwargs.keys()}

Expected kwargs: {expected_kwargs}"""

        if isinstance(inputs[0], dict):
            inputs = [inputs]
        
        if self._gpt_access.model_name == "o1-mini": # TODO: find a less hacky way to do this
            inputs = copy.deepcopy(inputs)
            for input in inputs:
                for i in range(len(input)):
                    if input[i]["role"] == "system":
                        input[i]["role"] = "user"
                    else:
                        break
        
        generation_results = GenerationResults()
        for text in inputs:
            generated_text = self.run_prompt(text, **kwargs)
            generated_text = [response["content"] for response in generated_text]
            result = GenerationResult(input_text=text, generated_text=generated_text)
            generation_results.results.append(result)

        return generation_results

    def parse_out(self, response: GenerationResults) -> typing.List[typing.List[str]]:
        return [[y for y in x.generated_text] for x in response.results]

if __name__ == '__main__':
    # Model from Hugging Face hub
    import os
    import numpy as np
    import json
    model_name = "gpt-4o-mini"
    model = GptModel(model_name)
    main_prompt = "Do simple math problems (Answer only the number and use '[END]' to finish the response):\nQuestion: 2 + 2\nAnswer: 4\n[END]"
    with model:
        for response in model.generate(
                [
                    [
                        {
                            "role": "user",
                            "content": f"{main_prompt}\nQuestion: 4 + 5\nAnswer:",
                        }
                    ],
                    [
                        {
                            "role": "user",
                            "content": f"{main_prompt}\nQuestion: 2 + 2\nAnswer:",
                        }
                    ],
                    [
                        {
                            "role": "user",
                            "content": f"{main_prompt}\nQuestion: 3 + 3 * 3\nAnswer:",
                        }
                    ]
                ],
                max_tokens=15,
                n=2,
                temperature=0.8,
                stop=["[END]"],
                # max_new_tokens=10,
                # temperature=0.1, # Nucleus sampling
                # do_sample=True, # Nucleus sampling
                # top_k=5, # Nucleus sampling
                # # num_beams=5, # Beam search
                # num_return_sequences=5,
                # stop_tokens=["[END]"],#, model._tokenizer.eos_token],
                # skip_special_tokens=True,
                # padding=True,
                # #truncation=True,
                # compute_probabilities=True,
                # return_full_text=False
                ):
            
            print("-" * 50)
            print(f"Prompt:\n{response.input_text[0]['content']}")
            for idx, result in enumerate(response.generated_text):
                print(f"Result [{idx + 1}]: {result}")
            print("-" * 50)
