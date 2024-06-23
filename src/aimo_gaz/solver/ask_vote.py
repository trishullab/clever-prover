from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from typing import Union
from aimo_gaz.solver.solver_config import vLLMHarness
from aimo_gaz.prompts.prompt import Prompt
import logging
import typing

class AskVote(Solver):
    def __init__(self, model: Union[vLLMHarness, Model], prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.history = []
        self.inference_kwargs["return_full_text"] = False # We only need the generated text coz we have the history
        self.inference_kwargs["stop_tokens"] = ["[END CODE]", "```", "<｜end▁of▁sentence｜>"]

    def solve(self, problem_description: str) -> int:
        raise NotImplementedError("This method is not implemented.")

    def solve_intermediate(self, problem_description: str, answers: list[int] = None) -> typing.Union[str, typing.List[str]]:
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model for the plan
        # if problem_description is not None and plan is not None:
        #     assert self.history == [], "History not empty (Code Solver)"
        #     message_problem = {"role": "user", "content": problem_description}
        #     message_plan = {"role": "user", "content": plan}
        #     self.history.append(message_problem)
        #     self.history.append(message_plan)
        # prompt = self.prompt.get_prompt(self.history)

        # match a letter with each answer
        choices = '\n'.join([f'( {chr(97+i)} ) {answer}' for i, answer in enumerate(answers)])
        prompt = f"""User: Below is a problem description. Which answer do you think is best?
        
Problem Description: 
{problem_description}

Choices:
{choices}

Assistant:"""

        self.logger.info(f"[CODE SOLVER] Raw prompt used:\n{prompt}")
        # Get the model response
        response = None
        try:
            response = self.model.generate(prompt, **self.inference_kwargs)
        except Exception as e:
            raise(e)
            response = None
            self.logger.exception("Encountered exception.")
        if response is None:
            generated_text = "Could not generate a response from the model."
            return generated_text
        outs = self.model.parse_out(response)
        generated_texts = []
        for result in outs:
            for gen_text in result:
                if gen_text.endswith('[END CODE]'):
                    generated_texts.append(gen_text.replace('[END CODE]', ''))
                elif gen_text.endswith('```'):
                    generated_texts.append(gen_text.replace('```', ''))
                elif gen_text.endswith('<｜end▁of▁sentence｜>'):
                    generated_texts.append(gen_text.replace('<｜end▁of▁sentence｜>', ''))
                else:
                    generated_texts.append(f"{gen_text}")
                self.logger.info(f"[CODE SOLVER] Generated text:\n{gen_text}")
        return generated_texts

    def add_response_to_history(self, generated_text: str):
        if self.history[-1]['role'] == "assistant":
            self.history[-1]['content'] += generated_text
        else:
            self.history.append({"role": "assistant", "content": generated_text})

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
