from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.utils import string_utils
import logging

class ImplementationPlannerTool(Tool):
    user_prompt_format = """[NL DESCRIPTION]
{}

[SPECIFICATION]
{}

[IMPLEMENTATION SIGNATURE]
{}

[TEST CASES]
{}"""

    def __init__(self, simple_prompter: SimplePrompter, logger: logging.Logger = None, **inference_kwargs):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        # self.inference_kwargs = inference_kwargs
        # self.inference_kwargs["n"] = 1 # Only one response is needed from planner tool
        # self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str) -> list[dict[str, str]]:
        # if not history or history[0]["role"] != "system":
        #     history.insert(0, {"role": "system", "content": self.system_prompt})
        #     history[1:1] = self.example_prompt_list
        history.append(
        {
            "role": "user",
            "content": ImplementationPlannerTool.user_prompt_format.format(
                problem_statement,
                problem_spec,
                implementation_signature,
                test_cases)
        })
        return history

    def parse_response(self, response: str) -> str:
        plan_start_ind = response.find("[IMPLEMENTATION PLAN]")
        if plan_start_ind != -1:
            plan_response = response[(plan_start_ind + len("[IMPLEMENTATION PLAN]")):]
        else:
            plan_response = response
        return plan_response.strip()

    def solve_intermediate(self, problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str) -> str:
        # Prompt the model for the plan
        self.history = self.get_prompt(self.history, problem_statement, problem_spec, implementation_signature, test_cases)
        self.logger.info(f"[IMPLEMENTATION PLANNER] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        message = self.history[-1]["content"]
        response = self.simple_prompter.run_prompt(message)
        self.history.append(response[0])
        generated_text = response[0]["content"]
        self.logger.info(f"[IMPLEMENTATION PLANNER] Raw response from model:\n{generated_text}")
        return self.parse_response(generated_text)

    def reset(self):
        self.history = []
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)