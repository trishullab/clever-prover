from clever_prover.solver.abs_solver_and_tool import Tool
from clever_prover.prompters.simple_prompter import SimplePrompter
import logging
import re

class SpecGeneratorTool(Tool):
    generated_implementation_regex = re.compile(r"\[GENERATED SPECIFICATION\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    def format_impl_prompt(
            problem_spec_nl : str,
            spec_signature: str,
            spec_plan: str = None,
    ):
        prompt = "[NL DESCRIPTION]\n" \
        f"{problem_spec_nl}\n" \
        "[SPECIFICATION SIGNATURE]\n" \
        f"{spec_signature}\n"
        if spec_plan is not None:
            prompt += "\n[SPEC PLAN]\n" \
            f"{spec_plan}"
        return prompt

    def __init__(self, 
        simple_prompter: SimplePrompter, 
        logger: logging.Logger = None):
        assert simple_prompter is not None, "Model must be provided."
        assert logger is not None, "Logger must be provided."
        self.simple_prompter = simple_prompter
        self.logger = logger
        self.history = []

    def parse_response(self, specification: list, logger: logging.Logger = None) -> str:
        """
        Parse the implementation string.
        """
        # Implement the logic to parse the implementation string
        # For example, split by newlines and filter out empty lines
        assert isinstance(specification, list), "implementation should be a list"
        assert len(specification) == 1, "implementation should be a single string"
        assert isinstance(specification[0], dict), "implementation should be a list of dicts"
        assert 'content' in specification[0], "implementation should contain 'content' key"
        assert isinstance(specification[0]['content'], str), "implementation content should be a string"
        original_implementation: str = specification[0]['content'].strip()
        if not original_implementation.endswith("[END]"):
            original_implementation += "\n[END]"
        logger = logger if logger else self.logger
        # Extract the generated implementation using regex
        match = self.generated_implementation_regex.search(original_implementation)
        if match:
            specification : str = match.group(1).strip()
        else:
            self.logger.warning("No generated implementation found in the response.")
            specification = original_implementation
        # defensive parsing
        implementation_lean_idx = specification.find("```lean")
        if implementation_lean_idx != -1:
            specification = specification[implementation_lean_idx + len("```lean"):]
            implementation_end_idx = specification.find("```")
            if implementation_end_idx != -1:
                specification = specification[:implementation_end_idx]
        specification = specification.strip()
        if specification.startswith("def"):
            # Find the first occurrence of ":=" and remove everything before it
            def_start_ind = specification.find(":=")
            if def_start_ind != -1:
                specification = specification[(def_start_ind + len(":=")):]
                specification = specification.strip()
        return specification

    def solve_intermediate(self, 
        problem_statement: str, 
        spec_signature: str, 
        spec_plan: str) -> str:
        # Prompt the model for the plan
        prompt = SpecGeneratorTool.format_impl_prompt(
            problem_statement,
            spec_signature,
            spec_plan)
        # Get the model response
        response = self.simple_prompter.run_prompt(prompt)
        generated_text = response[0]["content"]
        self.logger.info(f"[SPEC GENERATOR] Raw implementation generated:\n{generated_text}")
        return self.parse_response(response, self.logger)

    def reset(self):
        self.history = []
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        return super().__exit__(exc_type, exc_val, exc_tb)