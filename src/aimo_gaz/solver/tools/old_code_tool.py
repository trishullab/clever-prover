from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.models.gpt_model import GptModel
from aimo_gaz.prompts.prompt import Prompt
import logging
import typing

class OldCodeTool(Tool):
    def __init__(self, model: Model, prompt: Prompt, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompt is not None, "prompt must be provided."
        self.model = model
        self.prompt = prompt
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.history = []
        self.inference_kwargs["stop"] = ["[END CODE]", "```\n", "<｜end▁of▁sentence｜>"]

    def solve_intermediate(self, problem_description: str, plan: str = None) -> typing.Union[str, typing.List[str]]:
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the plan
        if problem_description is not None and plan is not None:
            assert self.history == [], "History not empty (Code Solver)"
            message_problem = {"role": "user", "content": problem_description}
            message_plan = {"role": "user", "content": plan}
            self.history.append(message_problem)
            self.history.append(message_plan)
        prompt = self.prompt.get_prompt(self.history)
        self.logger.info(f"[CODE TOOL] Raw prompt used:\n{prompt}")
        # Get the model response
        response = None
        try:
            response = self.model.generate(prompt, **self.inference_kwargs)
        except Exception as e:
            raise(e)
            # response = None
            # self.logger.exception("Encountered exception.")
        if response is None:
            generated_text = "Could not generate a response from the model."
            return generated_text
        outs = self.model.parse_out(response)
        generated_texts = []
        for result in outs:
            for gen_text in result:
                # if gen_text.endswith('[END CODE]'):
                #     generated_texts.append(gen_text.replace('[END CODE]', ''))
                # elif gen_text.endswith('```'):
                #     generated_texts.append(gen_text.replace('```', ''))
                # elif gen_text.endswith('<｜end▁of▁sentence｜>'):
                #     generated_texts.append(gen_text.replace('<｜end▁of▁sentence｜>', ''))
                # else:
                #     generated_texts.append(f"{gen_text}")
                actual_code_ind = gen_text.find("```python")
                if actual_code_ind != -1:
                    gen_text = gen_text[actual_code_ind + len("```python"):].strip()
                generated_texts.append(f"{gen_text}")
                self.logger.info(f"[CODE TOOL] Generated text:\n{gen_text}")
        return generated_texts

    def add_response_to_history(self, generated_text: str):
        if self.history[-1]['role'] == "assistant":
            self.history[-1]['content'] += generated_text
        else:
            self.history.append({"role": "assistant", "content": generated_text})

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)

if __name__ == "__main__":
    # Test the OldCodeTool class
    import time
    import os
    from aimo_gaz.prompts.old_code_prompt import OldCodePrompt
    from aimo_gaz.utils.log_utils import setup_logger

    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    os.makedirs(f".logs/{time_str}/temp", exist_ok=True)
    logger = setup_logger("aimo_gaz", f".logs/{time_str}/code_tool_test.log")

    # model_name_or_path = "deepseek-ai/deepseek-coder-1.3b-instruct"
    model_name = "gpt-4o"
    # model_logging_dir = ".logs/model"
    # model_args = {
    #     "no_init_eval": True,
    #     "padding": True,
    #     "truncation": True,
    #     "max_seq_length": 16384,
    #     "max_length": 16384,
    #     "load_model": True,
    #     "use_lora": False,
    #     "is_seq2seq": False,
    #     "token": None,
    #     "comet_experiment": None,
    #     # "base_device": 3
    # }
    # inference_args = {
    #     "max_new_tokens": 1024,
    #     "temperature": 0.9,
    #     "top_p": 1.0,
    #     "top_k": None,
    #     "do_sample": True,
    #     "num_return_sequences": 1,
    #     "max_length": 2048,
    #     "return_full_text": True, # We want the problem description to be returned as well
    #     "stop_tokens": ["[END]"]
    # }
    inference_args = {
        "max_tokens": 1024,
        "temperature": 0.9,
        "top_p": 1.0,
        "n": 1,
    }
    # model = Model(model_name_or_path, model_logging_dir, **model_args)
    model = GptModel(model_name)
    prompt = OldCodePrompt(system_prompt="", example_prompt="") # These are hard-coded in the class anyway
    tool = OldCodeTool(model, prompt, logger, **inference_args)
    problem_description = "Find the value of x in the equation 2x + 3 = 7."
    with tool:
        is_solved = False
        while not is_solved:
            # if not os.path.exists(f".logs/{time_str}/temp/plan.md"):
            #     with open(f".logs/{time_str}/temp/plan.md", "w") as f:
            #         f.write(problem_description)
            # input("Write the plan to solve the problem in file '.logs/temp/plan.md' and press enter.")
            # with open(f".logs/{time_str}/temp/plan.md", "r") as f:
            #     plan = f.read()
            plan = problem_description
            code = tool.solve_intermediate(problem_description, plan)
            # actual_code = code.find("```python code:")
            # actual_code = code[actual_code + len("```python code:"):].strip()
            # actual_code = actual_code[:-len("[END]")].strip() if actual_code.endswith("[END]") else actual_code
            actual_code = code[0]
            # dump the code in a file
            with open(f".logs/{time_str}/temp/code.py", "w") as f:
                f.write(actual_code)
            print(f"Run the command 'python .logs/{time_str}/temp/code.py'.")
            input("Run the code manually and press enter.")
            is_solved = input("Is the problem solved? (y/n): ").lower() == "y"
