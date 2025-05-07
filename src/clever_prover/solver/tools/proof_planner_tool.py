import typing
import logging
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.models.abs_model import Model
from clever_prover.prompters.prompter import Prompter
from clever_prover.utils import string_utils

class ProofPlannerTool(Tool):
    user_prompt_format_impl = """[NL DESCRIPTION]
{}

[SPECIFICATION]
{}

[IMPLEMENTATION]
{}

[THEOREM STATEMENT]
{}"""
    user_prompt_format_spec = """[NL DESCRIPTION]
{}

[GROUND TRUTH SPECIFICATION]
{}

[GENERATED SPECIFICATION]
{}

[THEOREM STATEMENT]
{}"""

    def __init__(self, 
            simple_prompter: SimplePrompter,
            logger: logging.Logger = None):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        self.history = []
    
    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, full_implementation_or_generated_spec: str, correctness_or_isomorphism_definition: str, is_impl_proof_planner: bool) -> list[dict[str, str]]:
        if is_impl_proof_planner:
            history.append({"role": "user", "content": ProofPlannerTool.user_prompt_format_impl.format(problem_statement, problem_spec, full_implementation_or_generated_spec, correctness_or_isomorphism_definition)})
        else:
            history.append({"role": "user", "content": ProofPlannerTool.user_prompt_format_spec.format(problem_statement, problem_spec, full_implementation_or_generated_spec, correctness_or_isomorphism_definition)})
        return history

    def parse_response(self, response: str, is_impl_proof_planner: bool):
        raw_response = response.strip()
        lemmas = []
        lemma_plans = []
        lemma_plan_start_ind = response.find("[HELPER LEMMA PLAN]")
        while lemma_plan_start_ind != -1:
            response = response[(lemma_plan_start_ind + len("[HELPER LEMMA PLAN]")):]
            lemma_start_ind = response.find("[HELPER LEMMA]")
            lemma_end_ind = response.find("[END HELPER LEMMA]")
            if lemma_start_ind != -1 and lemma_end_ind != -1 and lemma_start_ind < lemma_end_ind:
                lemma_plans.append(response[:lemma_start_ind].strip())
                lemmas.append(response[(lemma_start_ind + len("[HELPER LEMMA]")):lemma_end_ind].strip())
                response = response[(lemma_end_ind + len("[END HELPER LEMMA]")):]
            lemma_plan_start_ind = response.find("[HELPER LEMMA PLAN]")
        
        correctness_or_isomorphism_plan = "N/A"
        correctness_or_isomorphism_keyword = "[CORRECTNESS PLAN]" if is_impl_proof_planner else "[ISOMORPHISM PLAN]"
        correctness_or_isomorphism_plan_start_ind = response.find(correctness_or_isomorphism_keyword)
        if correctness_or_isomorphism_plan_start_ind != -1:
            correctness_or_isomorphism_plan_response = response[(correctness_or_isomorphism_plan_start_ind + len(correctness_or_isomorphism_keyword)):]
            correctness_or_isomorphism_plan = correctness_or_isomorphism_plan_response.strip()
        return raw_response, lemmas, lemma_plans, correctness_or_isomorphism_plan

    # def parse_response_thoughts(self, response: str):
    #     raw_response = response.strip()
    #     lemmas = []
    #     lemma_plans = []
        
    #     correctness_plan = "N/A"
    #     correctness_plan_start_ind = response.find("[THOUGHTS]")
    #     if correctness_plan_start_ind != -1:
    #         correctness_plan_response = response[(correctness_plan_start_ind + len("[THOUGHTS]")):]
    #         correctness_plan = correctness_plan_response.strip()
    #     return raw_response, lemmas, lemma_plans, correctness_plan

    def solve_intermediate(self,
        problem_statement: str,
        problem_spec: str,
        full_implementation_or_generated_spec: str,
        correctness_or_isomorphism_definition: str,
        is_impl_proof_planner: bool) -> typing.Tuple[str, list[str], list[str], str]:
        self.history = self.get_prompt(self.history, problem_statement, problem_spec, full_implementation_or_generated_spec, correctness_or_isomorphism_definition, is_impl_proof_planner)
        # Get the model response
        message = self.history[-1]["content"]
        response = self.simple_prompter.run_prompt(message)
        self.history.append(response[0])
        generated_text = response[0]["content"]
        self.logger.info(f"[PROOF PLANNER] Proof plan generated:\n{generated_text}")
        return self.parse_response(generated_text, is_impl_proof_planner) # if use_proof_planner else self.parse_response_thoughts(generated_text)

    def reset(self):
        self.history = []

    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)
