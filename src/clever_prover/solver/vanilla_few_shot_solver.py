from clever_prover.solver.abs_solver_and_tool import Solver
from clever_prover.models.abs_model import Model
from clever_prover.prompters.prompter import Prompter
from collections import Counter
import logging

class FewShotSolver(Solver):
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompter is not None, "prompter must be provided."
        self.model = model
        self.prompter = prompter
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.history = []
        if "problem_statement_message" not in self.inference_kwargs:
            self.inference_kwargs["problem_statement_message"] = "Below is a math problem you are to solve (positive numerical answer!):"

    def solve(self, problem_statement: str, time_allowed: int) -> int:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model with the problem description
        message = {"role": "user", "content": problem_statement}
        self.history.append(message)
        self.history = self.prompter.get_prompt(self.history)
        # Get the model's response
        response = None
        retry_count = 0
        inference_kwargs = self.inference_kwargs.copy()
        orig_num_return_sequences = self.inference_kwargs["num_return_sequences"]
        inference_num_return_sequences = orig_num_return_sequences
        while retry_count < 3 and response is None:
            try:
                response = self.model.generate(self.history, **inference_kwargs)
            except:
                response = None
                inference_kwargs["num_return_sequences"] = 1
                inference_num_return_sequences = 1
            retry_count += 1
        if response is None:
            return -1 # Maybe return the most common answer from the training data
        response = self.model.parse_out(response)

        assert len(response) > 0, "No response from the model."
        responses = response
        answers = []
        self.logger.info(f"Prompt:\n{self.history}")
        for resp in responses:
            for gen_text in resp:
                try:
                    self.logger.info(f"Generated text:\n{gen_text}")
                    self.logger.info(f"="*50)
                    answer = self.prompter.parse_response(gen_text)
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
