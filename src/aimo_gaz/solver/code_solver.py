from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.prompts.prompt import Prompt
import logging

class CodeSolver(Solver):
    def __init__(self, model: Model, prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
   
    def solve(self, problem_escription: str) -> int:
        raise NotImplementedError("This method is not implemented.")

    def solve_intermediate(self, problem_description: str) -> str:
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model for the plan
        prompt = self.prompt.get_prompt([{"role": "user", "content" : problem_description}])
        # Get the moel response
        try:
            response = self.model.generate(prompt, **self.inference_kwargs)
        except:
            response = None
        if response is None:
            return "Could not generate a response from the model."
        assert len(response.results) == 1, "No response (or too many responses) from the model."
        return response.results[0].generated_text[0] # We only need one response

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)

if __name__ == "__main__":
    # Test the PlannerSolver class
    import time
    import os
    from aimo_gaz.prompts.code_prompt import CodePrompt
    from aimo_gaz.tools.log_utils import setup_logger
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    os.makedirs(f".logs/{time_str}/temp", exist_ok=True)
    logger = setup_logger("aimo_gaz", f".logs/{time_str}/colde_solver_test.log")
    model_name_or_path = "deepseek-ai/deepseek-coder-1.3b-instruct"
    model_logging_dir = ".logs/model"
    model_args = {
        "no_init_eval": True,
        "padding": True,
        "truncation": True,
        "max_seq_length": 16384,
        "max_length": 16384,
        "load_model": True,
        "use_lora": False,
        "is_seq2seq": False,
        "token": None,
        "comet_experiment": None,
        # "base_device": 3
    }
    inference_args = {
        "max_new_tokens": 1024,
        "temperature": 0.9,
        "top_p": 1.0,
        "top_k": None,
        "do_sample": True,
        "num_return_sequences": 1,
        "max_length": 2048,
        "return_full_text": True, # We want the problem description to be returned as well
        "stop_tokens": ["[END]"] # TODO: Decide the stop token and probably mention it in the prompt class
    }
    model = Model(model_name_or_path, model_logging_dir, **model_args)
    prompt = CodePrompt(system_prompt="", example_prompt="") # These are hard-coded in the class anyway
    solver = CodeSolver(model, prompt, logger, **inference_args)
    problem_description = "Find the value of x in the equation 2x + 3 = 7."
    with solver:
        is_solved = False
        while not is_solved:
            if not os.path.exists(f".logs/{time_str}/temp/plan.md"):
                with open(f".logs/{time_str}/temp/plan.md", "w") as f:
                    f.write(problem_description)
            input("Write the plan to solve the problem in file .logs/temp/plan.md and press enter.")
            with open(f".logs/{time_str}/temp/plan.md", "r") as f:
                plan = f.read()
            code = solver.solve_intermediate(plan)
            actual_code = code.find("```python code:")
            actual_code = code[actual_code + len("```python code:"):].strip()
            actual_code = actual_code[:-len("[END]")].strip() if actual_code.endswith("[END]") else actual_code
            # dump the code in a file
            with open(f".logs/{time_str}/temp/code.py", "w") as f:
                f.write(actual_code)
            print(f"Run the command python .logs/{time_str}/temp/code.py.")
            input("Run the code manually and press enter.")
            is_solved = input("Is the problem solved? (y/n): ").lower() == "y"
    pass