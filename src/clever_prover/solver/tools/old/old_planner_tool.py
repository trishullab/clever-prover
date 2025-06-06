from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.models.abs_model import Model
from clever_prover.models.gpt_model import GptModel
# from clever_prover.solver.solver_and_tool_config import vLLMHarness
from clever_prover.prompters.prompter import Prompter
import logging

class OldPlannerTool(Tool):
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompter is not None, "prompter must be provided."
        self.model = model
        self.prompter = prompter
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.inference_kwargs["n"] = 1 # Only one response is needed from planner tool
        self.inference_kwargs["stop"] = ["[END PROCEDURE]", "7.", "the answer is", "<｜end▁of▁sentence｜>"]
        self.history = []

    def solve_intermediate(self, problem_statement: str) -> str:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the plan
        message = {"role": "user", "content": problem_statement}
        self.history.append(message)
        self.history = self.prompter.get_prompt(self.history)
        self.logger.info(f"[PLANNER] Raw prompt used:\n{self.history}")
        # Get the model response
        # response = None
        # try:
        #     response = self.model.generate(prompt, **self.inference_kwargs)
        # except Exception as e:
        #     raise(e)
        #     # response = None
        #     # self.logger.exception("Encountered exception.")
        response = self.model.generate(self.history, **self.inference_kwargs)
        # if response is None:
        #     generated_text = "Could not generate a response from the model."
        #     outs = [[generated_text]]
        # else:
        #     outs = self.model.parse_out(response)
        #     generated_text = outs[0][0]
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        if self.history[-1]['role'] == "assistant":
            self.history[-1]['content'] += generated_text
        else:
            self.history.append({"role": "assistant", "content": generated_text})
        # if not generated_text.strip().endswith("[END PROCEDURE]"):
        #     generated_text = generated_text.rstrip('\n') + "\n[END PROCEDURE]"
        # self.logger.info(f"[PLANNER] Plan generated:\n{generated_text}")
        # return generated_text.replace('[END PROCEDURE]', '')
        generated_text = generated_text.rstrip("\n") + "\n" # TODO: Is adding the extra newline necessary?
        self.logger.info(f"[PLANNER] Plan generated:\n{generated_text}")
        return generated_text

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)

if __name__ == "__main__":
    # Test the OldPlannerTool class
    from clever_prover.prompters.old_planner_prompter import OldPlannerPrompter
    from clever_prover.utils.log_utils import setup_logger
    import time
    import os

    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    logger = setup_logger("clever_prover", f".logs/{time_str}/planner_tool_test.log")

    # model_name_or_path = "deepseek-ai/deepseek-math-7b-rl" # "deepseek-ai/deepseek-math-7b-rl" #"deepseek-ai/deepseek-coder-1.3b-instruct"
    model_name = "gpt-4o-mini"
    # model_logging_dir = ".logs/model"

    # model_args = {
    #     "no_init_eval": True,
    #     "padding": True,
    #     "truncation": True,
    #     "max_seq_length": 4096, # 16384
    #     "max_length": 4096, # 16384
    #     "load_model": True,
    #     "use_lora": True,
    #     "is_seq2seq": False,
    #     "token": None,
    #     "comet_experiment": None,
    #     "base_device": 0
    # }
    # inference_args = {
    #     "max_new_tokens": 1024,
    #     "temperature": 0.7,
    #     "top_p": 1.0,
    #     "top_k": None,
    #     "do_sample": True,
    #     "num_return_sequences": 1,
    #     "max_length": 2048,
    #     "return_full_text": True, # We want the problem description to be returned as well
    #     "stop_tokens": ["[END PROCEDURE]", "\n\n"]
    # }
    inference_args = {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0,
    }
    use_vllm = False
    if use_vllm:
        # vllm_model_args = {
        #     "dtype": "float16", "gpu_memory_utilization": 0.95, "tensor_parallel_size": 2, 'max_model_len':1024, #"tokenizer": "deepseek-ai/deepseek-coder-1.3b-instruct",
        #     "speculative_model": "deepseek-ai/deepseek-coder-1.3b-instruct", "num_speculative_tokens": 5, "use_v2_block_manager": True
        # }
        # model = vLLMHarness.load_from_config(model_name_or_path, vllm_model_args, vllm_inference_args)
        # prompt = OldPlannerPrompter(system_prompt="", example_prompt=[])  # These are hard-coded in the class anyway
        # problem_statement = "There exists a unique increasing geometric sequence of five 2-digit positive integers. What is their sum?"
        # tool = OldPlannerTool(model, prompt)
        assert False
    else:
        # model = GptModel(model_name_or_path, model_logging_dir, **model_args)
        model = GptModel(model_name)
        prompter = OldPlannerPrompter(system_prompt="", example_prompt=[])  # These are hard-coded in the class anyway
        problem_statement = "There exists a unique increasing geometric sequence of five 2-digit positive integers. What is their sum?"
        tool = OldPlannerTool(model, prompter, logger, **inference_args)

    with tool:
        is_solved = False
        max_tries = 1
        current_tries = 0
        while not is_solved and current_tries < max_tries:
            current_tries += 1
            start = time.time()
            plan = tool.solve_intermediate(problem_statement)
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
            # problem_statement = new_plan
            # is_solved = input("Is the problem solved? (y/n): ").lower() == "y"
