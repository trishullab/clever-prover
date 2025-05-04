import typing
import logging
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.models.abs_model import Model
from clever_prover.prompters.prompter import Prompter
from clever_prover.utils import string_utils

class FewShotProverTool(Tool):
    user_prompt_format = """[NL DESCRIPTION]
{}

[SPECIFICATION]
{}

[IMPLEMENTATION]
{}

[THEOREM STATEMENT]
{}

[PROOF PLAN]
{}"""

    def __init__(self, 
            simple_prompter: SimplePrompter,
            logger: logging.Logger = None, 
            **inference_kwargs):
        assert simple_prompter is not None, "Model must be provided."
        # assert model is not None, "Model must be provided."
        # assert prompter is not None, "Prompter must be provided."
        assert logger is not None, "Logger must be provided."
        # self.model = model
        # self.prompter = prompter
        self.simple_prompter = simple_prompter
        self.logger = logger
        # self.inference_kwargs = inference_kwargs
        # self.inference_kwargs["n"] = 1 # Only one response is needed from planner tool
        # self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []
    
    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, implementation_signature: str, implementation: str, theorem_statement: str, proof_plan: str) -> list[dict[str, str]]:
        # if not history or history[0]["role"] != "system":
        #     history.insert(0, {"role": "system", "content": self.system_prompt})
        #     history[1:1] = self.example_prompt_list
        full_implementation = implementation_signature + "\n" + implementation
        history.append({"role": "user", "content": FewShotProverTool.user_prompt_format.format(problem_statement, problem_spec, full_implementation, theorem_statement, proof_plan)})
        return history

    def parse_response(self, response: str):
        proof = "by sorry"
        proof_start_ind = response.find("[PROOF]")
        if proof_start_ind != -1:
            proof_response = response[(proof_start_ind + len("[PROOF]")):]
            proof = proof_response.strip()
        return proof

    def solve_intermediate(self, problem_statement: str, problem_spec: str, implementation_signature: str, implementation: str, theorem_statement: str, proof_plan: str) -> typing.Tuple[str, list[str], list[str], str]:
        # if not self.model.is_loaded():
        #     self.model.__enter__()
        # Prompt the model for the plan
        self.history = self.get_prompt(self.history, problem_statement, problem_spec, implementation_signature, implementation, theorem_statement, proof_plan)
        # Get the model response
        message = self.history[-1]["content"]
        self.logger.info(f"[FEW SHOT PROVER] Raw prompt used:\n{message}")
        response = self.simple_prompter.run_prompt(message)
        self.history.append(response[0])
        generated_text = response[0]["content"]
        self.logger.info(f"[FEW SHOT PROVER] Proof generated:\n{generated_text}")
        return self.parse_response(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)
