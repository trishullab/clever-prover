import typing
import logging
import re
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.solver.abs_solver_and_tool import Tool

class FewShotImplProverTool(Tool):
    generated_proof_regex = re.compile(r"\[PROOF\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    def format_prompt(self, 
    problem_spec_nl: str, 
    problem_spec_formal_ground_truth: str, 
    implementation: str, 
    theorem_statement: str,
    proof_plan: str = None) -> str:
        prompt = "[NL DESCRIPTION]\n" \
        f"{problem_spec_nl}\n" \
        "[SPECIFICATION]\n" \
        f"{problem_spec_formal_ground_truth}\n" \
        "[IMPLEMENTATION]\n" \
        f"{implementation}\n" \
        "[THEOREM STATEMENT]\n" \
        f"{theorem_statement}"
        if proof_plan is not None:
            prompt += "\n[PROOF PLAN]\n" \
            f"{proof_plan}"
        return prompt

    def __init__(self, 
            simple_prompter: SimplePrompter,
            logger: logging.Logger = None):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        self.history = []
    
    def parse_response(self, proof: list, logger: logging.Logger = None) -> str:
        """
        Parse the proof string into a list of lemmas.
        """
        # Implement the logic to parse the proof string
        # For example, split by newlines and filter out empty lines
        assert isinstance(proof, list), "proof should be a list"
        assert len(proof) == 1, "proof should be a single string"
        assert isinstance(proof[0], dict), "proof should be a list of dicts"
        assert 'content' in proof[0], "proof should contain 'content' key"
        assert isinstance(proof[0]['content'], str), "proof content should be a string"
        original_proof: str = proof[0]['content'].strip()
        if not original_proof.endswith("[END]"):
            original_proof += "\n[END]"
        logger = logger if logger else self.logger
        # Extract the generated spec using regex
        match = self.generated_proof_regex.search(original_proof)
        if match:
            proof = match.group(1).strip()
        else:
            self.logger.warning("No generated proof found in the response.")
            proof = "sorry"
        return proof

    def solve_intermediate(self, 
        problem_statement: str, 
        problem_spec: str,  
        implementation: str, 
        theorem_statement: str,
        proof_plan: str = None) -> typing.Tuple[str, list[str], list[str], str]:
        prompt = self.format_prompt(
            problem_statement, 
            problem_spec, 
            implementation,
            theorem_statement, 
            proof_plan)
        response = self.simple_prompter.run_prompt(prompt)
        generated_text = response[0]["content"]
        self.logger.info(f"[FEW SHOT PROVER] Proof generated:\n{generated_text}")
        return self.parse_response(response, self.logger)

    def reset(self):
        self.history = []

    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)
