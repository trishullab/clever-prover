from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.prompters.simple_prompter import SimplePrompter
import logging
import re

class ImplementerTool(Tool):
    generated_implementation_regex = re.compile(r"\[GENERATED IMPLEMENTATION\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    def format_impl_prompt(
            problem_spec_nl : str,
            problem_spec_formal_ground_truth: str,
            implementation_signature: str,
            test_cases_lean: str,
            implementation_plan: str = None,
    ):
        prompt = "[NL DESCRIPTION]\n" \
        f"{problem_spec_nl}\n" \
        "[SPECIFICATION]\n" \
        f"{problem_spec_formal_ground_truth}\n" \
        "[IMPLEMENTATION SIGNATURE]\n" \
        f"{implementation_signature}\n" \
        "[TEST CASES]\n" \
        f"{test_cases_lean}"
        if implementation_plan is not None:
            prompt += "\n[IMPLEMENTATION PLAN]\n" \
            f"{implementation_plan}"
        return prompt

    def __init__(self, 
        simple_prompter: SimplePrompter, 
        logger: logging.Logger = None):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        self.history = []

    def parse_response(self, implementation: list, logger: logging.Logger = None) -> str:
        """
        Parse the implementation string.
        """
        # Implement the logic to parse the implementation string
        # For example, split by newlines and filter out empty lines
        assert isinstance(implementation, list), "implementation should be a list"
        assert len(implementation) == 1, "implementation should be a single string"
        assert isinstance(implementation[0], dict), "implementation should be a list of dicts"
        assert 'content' in implementation[0], "implementation should contain 'content' key"
        assert isinstance(implementation[0]['content'], str), "implementation content should be a string"
        original_implementation: str = implementation[0]['content'].strip()
        if not original_implementation.endswith("[END]"):
            original_implementation += "\n[END]"
        logger = logger if logger else self.logger
        # Extract the generated implementation using regex
        match = self.generated_implementation_regex.search(original_implementation)
        if match:
            implementation : str = match.group(1).strip()
        else:
            self.logger.warning("No generated implementation found in the response.")
            implementation = original_implementation
        # defensive parsing
        implementation_lean_idx = implementation.find("```lean")
        if implementation_lean_idx != -1:
            implementation = implementation[implementation_lean_idx + len("```lean"):]
            implementation_end_idx = implementation.find("```")
            if implementation_end_idx != -1:
                implementation = implementation[:implementation_end_idx]
        implementation = implementation.strip()
        if implementation.startswith("def"):
            # Find the first occurrence of ":=" and remove everything before it
            def_start_ind = implementation.find(":=")
            if def_start_ind != -1:
                implementation = implementation[(def_start_ind + len(":=")):]
                implementation = implementation.strip()
        return implementation

    def solve_intermediate(self, 
        problem_statement: str, 
        problem_spec: str, 
        implementation_signature: str, 
        test_cases: str, 
        implementation_plan: str) -> str:
        # Prompt the model for the plan
        prompt = ImplementerTool.format_impl_prompt(
            problem_statement,
            problem_spec,
            implementation_signature,
            test_cases,
            implementation_plan)
        # Get the model response
        response = self.simple_prompter.run_prompt(prompt)
        generated_text = response[0]["content"]
        self.logger.info(f"[IMPLEMENTER] Raw implementation generated:\n{generated_text}")
        return self.parse_response(response, self.logger)

    def reset(self):
        self.history = []
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)