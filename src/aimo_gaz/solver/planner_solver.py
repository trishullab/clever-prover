from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.prompts.prompt import Prompt
from collections import Counter
import logging

class PlannerSolver(Solver):
    def __init__(self, model: Model, prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        if "problem_description_message" not in self.inference_kwargs:
            raise NotImplementedError
            # self.inference_kwargs["problem_description_message"]    
    def solve_intermediate(self, problem_escription: str):
        raise NotImplementedError

    # TODO: George: Maybe this should never be called?
    def solve(self, problem_description: str):
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model for the plan
        problem_description_message = str(self.inference_kwargs["problem_description_message"])
        prompt = self.prompt.get_prompt([{problem_description_message : problem_description}])
        # Get the moel response
        try:
            response = self.model.generate(prompt, **inference_kwargs)
        except:
            response = None
        if response is None:
            return -1 # Plan was not generated
        assert len(response.results) == 1, "No response (or too many responses) from the model."
        return response

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)