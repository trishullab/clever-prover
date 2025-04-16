import typing
from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.models.abs_model import Model
from clever_prover.prompters.prompter import Prompter
from clever_prover.utils import string_utils
import logging

class ProofPlannerTool(Tool):
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

    def solve_intermediate(self, problem_statement: str, problem_spec: str, implementation: str, correctness_definition: str) -> typing.Union[str, list[str], list[str], str]:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the plan
        self.history = self.prompter.get_prompt(self.history, problem_statement, problem_spec, implementation, correctness_definition)
        self.logger.info(f"[PROOF PLANNER] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        response = self.model.generate(self.history, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info("[PROOF PLANNER] Proof plan generated.")
        return self.prompter.parse_response(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
