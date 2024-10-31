from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.prompts.prompt import Prompt
import logging

class CoordinatorTool(Tool):
    def __init__(self, model: Model, prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.inference_kwargs["n"] = 1 # Only one response is needed from coordinator agent
        self.inference_kwargs["stop"] = []
        self.history = []

    def solve_intermediate(self, problem_description: str) -> str:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the plan
        message = {"role": "user", "content": problem_description}
        self.history.append(message)
        prompt = self.prompt.get_prompt(self.history)
        self.logger.info(f"[COORDINATOR] Raw prompt used:\n{prompt}")
        # Get the model response
        response = self.model.generate(prompt, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info(f"[COORDINATOR] Output generated: {generated_text}")
        return self.prompt.parse_response(f"{generated_text}")

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)
