from enum import Enum
import typing
from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.models.abs_model import Model
from clever_prover.prompters.prompter import Prompter
from clever_prover.scripts.eval import ProblemState
from clever_prover.utils import string_utils
import logging

class ToolOrOther(Enum):
    PLANNER = "planner"
    CODER = "coder"
    LLM_GUESSER = "llm_guesser"
    PROVER = "prover"

class CoordinatorTool(Tool):
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "Model must be provided."
        assert prompter is not None, "Prompter must be provided."
        assert logger is not None, "Logger must be provided."
        self.model = model
        self.prompter = prompter
        self.logger = logger
        self.inference_kwargs = inference_kwargs
        self.inference_kwargs["n"] = 1 # Only one response is needed from coordinator tool
        self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def solve_intermediate(self, history_buffer: list[str], problem_statement: str, theorem_statement: str, problem_state: ProblemState) -> typing.Tuple[ToolOrOther, str, float]:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the tool
        self.history = self.prompter.get_prompt(self.history, history_buffer, problem_statement, theorem_statement, problem_state)
        self.logger.info(f"[COORDINATOR] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        self.inference_kwargs["stop"] = self.prompter.stop_tokens
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
