from enum import Enum
import typing
from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.scripts.eval import ProblemState
from aimo_gaz.utils import string_utils
import logging

class ToolOrOther(Enum):
    PLANNER = "planner"
    CODER = "coder"
    LLM_GUESSER = "llm_guesser"
    PROVER = "prover"

class CoordinatorTool(Tool):
    def __init__(self, model: Model, prompter: Prompter, format_answer_prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "Model must be provided."
        assert prompter is not None, "Prompter must be provided."
        assert logger is not None, "Logger must be provided."
        self.model = model
        self.prompter = prompter
        self.format_answer_prompter = format_answer_prompter
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

    def solve_intermediate_format_answer(self, history_buffer: list[str], theorem_statement: str) -> str:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the tool
        self.history = self.format_answer_prompter.get_prompt(self.history, history_buffer, theorem_statement)
        self.logger.info(f"[COORDINATOR] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        self.inference_kwargs["stop"] = self.format_answer_prompter.stop_tokens
        response = self.model.generate(self.history, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info(f"[COORDINATOR] Output generated: {generated_text}")
        return self.format_answer_prompter.parse_response(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
