from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.models.model import Model
from aimo_gaz.solver.solver_config import vLLMHarness
from aimo_gaz.prompts.prompt import Prompt
from typing import Union
import logging

class PlannerSolver(Solver):
    def __init__(self, model: Union[vLLMHarness, Model], prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.inference_kwargs["num_return_sequences"] = 1 # Only one response is needed from planner agent
        self.inference_kwargs["return_full_text"] = False # We only need the generated text coz we have the history
        self.inference_kwargs["stop_tokens"] = ["[END PROCEDURE]", "7.", "the answer is", "\n\n", "<｜end▁of▁sentence｜>"]
        self.history = []

    def solve(self, problem_description: str) -> int:
        raise NotImplementedError("This method is not implemented.")

    def solve_intermediate(self, problem_description: str) -> str:
        if not self.model._is_loaded:
            self.model.__enter__()
        # Prompt the model for the plan
        message = {"role": "user", "content": problem_description}
        self.history.append(message)
        prompt = self.prompt.get_prompt(self.history)
        self.logger.info(f"[PLANNER] Raw prompt used:\n{prompt}")
        # Get the moel response
        response = None
        try:
            response = self.model.generate(prompt, **self.inference_kwargs)
        except Exception as e:
            raise(e)
            response = None
            self.logger.exception("Encountered exception.")
        if response is None:
            generated_text = "Could not generate a response from the model."
            outs = [[generated_text]]
        else:
            outs = self.model.parse_out(response)
            generated_text = outs[0][0]
        if self.history[-1]['role'] == "assistant":
            self.history[-1]['content'] += generated_text
        else:
            self.history.append({"role": "assistant", "content": generated_text})
        assert len(outs) == 1, "No response (or too many responses) from the model."
        if not generated_text.strip().endswith("[END PROCEDURE]"):
            generated_text = generated_text.rstrip('\n') + "\n[END PROCEDURE]"
        self.logger.info(f"[PLANNER] Plan generated:\n{generated_text}")
        return f"1. {generated_text.replace('[END PROCEDURE]', '')}"
        # generated_text

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)

if __name__ == "__main__":
    # Test the PlannerSolver class
    from aimo_gaz.prompts.planner_prompt import PlannerPrompt
    import time

    model_name_or_path = "deepseek-ai/deepseek-math-7b-rl" # "deepseek-ai/deepseek-math-7b-rl" #"deepseek-ai/deepseek-coder-1.3b-instruct"
    model_logging_dir = ".logs/model"

    model_args = {
        "no_init_eval": True,
        "padding": True,
        "truncation": True,
        "max_seq_length": 4096, # 16384
        "max_length": 4096, # 16384
        "load_model": True,
        "use_lora": True,
        "is_seq2seq": False,
        "token": None,
        "comet_experiment": None,
        "base_device": 0
    }
    inference_args = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0,
        "top_k": None,
        "do_sample": True,
        "num_return_sequences": 1,
        "max_length": 2048,
        "return_full_text": True, # We want the problem description to be returned as well
        "stop_tokens": ["[END PROCEDURE]", "\n\n"] # TODO: Decide the stop token and probably mention it in the prompt class
    }
    vllm_inference_args = {
        "max_tokens": 512,
        "temperature": 0.9,
        "top_p": 1.0,
        # "top_k": None,
        # "do_sample": True,
        "n": 1,
        # "max_length": 2048,
        # "return_full_text": True, # We want the problem description to be returned as well
        "stop_token_ids": ["[END]"] # TODO: Decide the stop token and probably mention it in the prompt class
    }
    use_vllm = True
    if use_vllm:
        vllm_model_args = {
            "dtype": "float16", "gpu_memory_utilization": 0.95, "tensor_parallel_size": 2, 'max_model_len':1024, #"tokenizer": "deepseek-ai/deepseek-coder-1.3b-instruct",
            "speculative_model": "deepseek-ai/deepseek-coder-1.3b-instruct", "num_speculative_tokens": 5, "use_v2_block_manager": True
        }
        model = vLLMHarness.load_from_config(model_name_or_path, vllm_model_args, vllm_inference_args)
        prompt = PlannerPrompt(system_prompt="", example_prompt="")  # These are hard-coded in the class anyway
        problem_description = "There exists a unique increasing geometric sequence of five 2-digit positive integers. What is their sum?"
        solver = PlannerSolver(model, prompt)
    else:
        model = Model(model_name_or_path, model_logging_dir, **model_args)
        prompt = PlannerPrompt(system_prompt="", example_prompt="")  # These are hard-coded in the class anyway
        problem_description = "There exists a unique increasing geometric sequence of five 2-digit positive integers. What is their sum?"
        solver = PlannerSolver(model, prompt, **inference_args)

    with solver:
        is_solved = False
        max_tries = 5
        current_tries = 0
        while not is_solved and current_tries < max_tries:
            current_tries += 1
            start = time.time()
            plan = solver.solve_intermediate(problem_description)
            end = time.time()
            print(f"Time taken to generate the plan: {end - start} seconds.")
            print(plan)
            print("-"*50)
            # To do elaborate testing, after the plan with custom code
            # potnetially read code from a fix file which you modify
            # based on the plan
            # with open(".logs/temp/code.py", "r") as f:
            #     code = f.read()
            # input("Press enter to continue after running the code manually. Please dump the output in .logs/temp/output.txt")
            # with open(".logs/temp/output.txt", "r") as f:
            #     output = f.read()
            # new_plan = plan + "\n```python code:\n" + code + "\n```output:\n" + output
            # # Now prompt the model with the new plan
            # problem_description = new_plan
            # is_solved = input("Is the problem solved? (y/n): ").lower() == "y"
    pass