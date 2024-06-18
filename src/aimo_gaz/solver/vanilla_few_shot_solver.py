from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.prompts.prompt import Prompt

class FewShotSolver(Solver):
    def __init__(self, model: Model, prompt: Prompt, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs

    def solve(self, problem_description: str):
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model with the problem description
        prompt = self.prompt.get_prompt([{"": problem_description}])
        # Get the model's response
        response = self.model.generate(prompt, **self.inference_kwargs)
        assert len(response.results) > 0, "No response from the model."
        response = response.results
        if "stop_tokens" in self.inference_kwargs:
            for stop_token in self.inference_kwargs["stop_tokens"]:
                if response[0].generated_text[0].endswith(stop_token):
                    return response[0].generated_text[0].rstrip(stop_token)
        return response[0].generated_text[0]
    
    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)