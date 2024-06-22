from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.prompts.prompt import Prompt
from collections import Counter
import logging

class FewShotSolver(Solver):
    def __init__(self, model: Model, prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        if "problem_description_message" not in self.inference_kwargs:
            self.inference_kwargs["problem_description_message"] = "Below is a math problem you are to solve (positive numerical answer!):"

    def solve(self, problem_description: str) -> int:
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model with the problem description
        problem_description_message = str(self.inference_kwargs["problem_description_message"])

        prompt = self.prompt.get_prompt([{'role': 'user', 'content': problem_description}])
        # Get the model's response
        response = None
        retry_count = 0
        inference_kwargs = self.inference_kwargs.copy()
        orig_num_return_sequences = self.inference_kwargs["num_return_sequences"]
        inference_num_return_sequences = orig_num_return_sequences
        while retry_count < 3 and response is None:
            try:
                response = self.model.generate(prompt, **inference_kwargs)
            except:
                response = None
                inference_kwargs["num_return_sequences"] = 1
                inference_num_return_sequences = 1
            retry_count += 1
        if response is None:
            return -1 # Maybe return the most common answer from the training data
        assert len(response.results) > 0, "No response from the model."
        responses = response.results
        answers = []
        self.logger.info(f"Prompt:\n{prompt}")
        for resp in responses:
            for gen_text in resp.generated_text:
                try:
                    self.logger.info(f"Generated text:\n{gen_text}")
                    self.logger.info(f"="*50)
                    answer = self.prompt.parse_response(gen_text)
                    try:
                        answer = float(answer)
                    except:
                        answer = None
                    if answer is not None:
                        answers.append(int(answer) % 1000)
                except:
                    pass
        # Take the answer which comes most frequently
        if len(answers) == 0:
            return -1 # Maybe return the most common answer from the training data
        answer_counter = Counter(answers)
        most_common_answer = answer_counter.most_common(1)[0][0]
        return most_common_answer
    
    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)

    def solve_intermediate(self, problem_description: str):
        raise NotImplementedError("solve_intermediate is not implemented for FewShotSolver.")