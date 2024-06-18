from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.models.prompt import Prompt

class FewShotSolver(Solver):
    def __init__(self, model: Model, prompt: Prompt, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs

    def solve(self, problem_description: str):
        # Prompt the model with the problem description
        prompt = self.prompt.get_prompt([{"problem": problem_description}])
        # Get the model's response
        response = self.model.generate(prompt, **self.inference_kwargs)
        responses = [resp for resp in response]
        # argmax on neg_log_likelihood
        likelihoods = [resp["neg_log_likelihood"] for resp in responses]
        best_response = responses[likelihoods.index(min(likelihoods))]
        return best_response.generated_text