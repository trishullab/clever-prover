import typing
from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.utils import string_utils
import logging

class PlannerTool(Tool):
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "Model must be provided."
        assert prompter is not None, "Prompter must be provided."
        assert logger is not None, "Logger must be provided."
        self.model = model
        self.prompter = prompter
        self.logger = logger
        self.inference_kwargs = inference_kwargs
        self.inference_kwargs["n"] = 1 # Only one response is needed from planner tool
        self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def solve_intermediate(self, tool_prompt: str) -> typing.Tuple[str, float]:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the plan
        self.history = self.prompter.get_prompt(self.history, tool_prompt)
        self.logger.info(f"[PLANNER] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        response = self.model.generate(self.history, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info("[PLANNER] Plan generated.")
        return self.prompter.parse_response(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
