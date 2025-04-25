from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.prompters.prompter import Prompter
from clever_prover.utils import string_utils
import logging

class ImplementerTool(Tool):
    prompt_format = """[PROBLEM STATEMENT]
{}
[END]

[PROBLEM SPEC]
{}
[END]

[FUNCTION IMPLEMENTATION SIGNATURE]
{}
[END]

[TEST CASES]
{}
[END]

[PLAN]
{}
[END]"""
    def __init__(self, simple_prompter: SimplePrompter, logger: logging.Logger = None, **inference_kwargs):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        # self.inference_kwargs = inference_kwargs
        # self.inference_kwargs["n"] = 1 # Only one response is needed from planner tool
        # self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str, implementation_plan: str) -> list[dict[str, str]]:
        # if not history or history[0]["role"] != "system":
        #     history.insert(0, {"role": "system", "content": self.system_prompt})
        #     history[1:1] = self.example_prompt_list
        history.append(
        {
            "role": "user", 
            "content": ImplementerTool.prompt_format.format(
                problem_statement, 
                problem_spec, 
                implementation_signature, 
                test_cases, 
                implementation_plan)
        })
        return history

    def parse_response(self, response: str) -> str:
        def_start_ind = response.find("```lean")
        if def_start_ind != -1:
            def_response = response[(def_start_ind + len("```lean")):]
            def_end_ind = def_response.find("```")
            if def_end_ind != -1:
                def_response = def_response[:def_end_ind]
        else:
            def_response = response
        def_response = def_response.strip()
        if def_response.startswith("def"):
            # Find the first occurrence of ":=" and remove everything before it
            def_start_ind = def_response.find(":=")
            if def_start_ind != -1:
                def_response = def_response[def_start_ind + len(":="):]
                def_response = def_response.strip()
        return def_response

    def solve_intermediate(self, problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str, implementation_plan: str) -> str:
        # Prompt the model for the plan
        self.history = self.get_prompt(
            self.history, 
            problem_statement, 
            problem_spec, 
            implementation_signature, 
            test_cases, 
            implementation_plan)
        # Get the model response
        message = self.history[-1]["content"]
        self.logger.info(f"[IMPLEMENTER] Raw prompt used:\n{message}")
        response = self.simple_prompter.run_prompt(message)
        self.history.append(response[0])
        generated_text = response[0]["content"]
        self.logger.info(f"[IMPLEMENTER] Raw implementation generated:\n{generated_text}")
        return self.parse_response(generated_text)

    def reset(self):
        self.history = []
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)