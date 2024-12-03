from enum import Enum
import typing
from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.prompters.prompter import Prompter
import logging

class ToolOrGlobalGuess(Enum):
    PLANNER = "planner"
    CODER = "coder"
    LLM_GUESSER = "llm_guesser"
    GLOBAL_GUESS = "global_guess"
    PROVER = "prover"

class CoordinatorTool(Tool):
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompter is not None, "prompter must be provided."
        self.model = model
        self.prompter = prompter
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.inference_kwargs["n"] = 1 # Only one response is needed from coordinator tool
        self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def solve_intermediate(self, problem_description: str) -> typing.Tuple[ToolOrGlobalGuess, str, float]:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the tool
        self.history = self.prompter.get_prompt(self.history, problem_description)
        if len(self.history) > 10: # TODO: move this pattern into string_utils
            self.logger.info("[COORDINATOR] Raw prompt used:\n[...,\n{}]".format(",\n".join(map(str, self.history[-10:]))))
        else:
            self.logger.info("[COORDINATOR] Raw prompt used:\n[{}]".format(",\n".join(map(str, self.history))))
        # Get the model response
        response = self.model.generate(self.history, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info(f"[COORDINATOR] Output generated: {generated_text}")
        return self.prompter.parse_response(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
