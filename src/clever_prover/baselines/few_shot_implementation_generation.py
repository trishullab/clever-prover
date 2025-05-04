import logging
import os
import re
from clever_prover.tasks.implementation_generation_task import ImplementationGenerationTask
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_bench.task import ProblemViewTask
from clever_bench.lean_problem import format_problem_as_lean_with_line_ranges, Lemma
from clever_prover.prompters.simple_prompter import SimplePrompter

class FewShotImplementationGenerationTask(ImplementationGenerationTask):
    generated_implementation_regex = re.compile(r"\[GENERATED IMPLEMENTATION\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    generated_helper_lemmas_regex = re.compile(r"\[HELPER LEMMAS\]\s*([\s\S]*?)\s*\[END LEMMAS\]", re.MULTILINE)
    generated_proof_regex = re.compile(r"\[PROOF\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    def __init__(self, 
        problem_id: int,
        problem_view: ProblemViewTask,
        impl_prompt_settings: PromptSettings,
        impl_model_settings: ModelSettings,
        proof_prompt_settings: PromptSettings,
        proof_model_settings: ModelSettings,
        lemma_name="correctness",
        logger: logging.Logger = None):
        """
        Initialize the FewShotImplementationGenerationTask with project path, file path, and lemma name.
        """
        super().__init__(problem_id=problem_id, problem_view=problem_view, lemma_name=lemma_name, logger=logger)
        self.proof_prompt_settings = proof_prompt_settings
        self.proof_model_settings = proof_model_settings
        self.impl_prompt_settings = impl_prompt_settings
        self.impl_model_settings = impl_model_settings
        self.generated_implementation = None
        self.helper_lemmas = None
        self.generated_proof = None

    def parse_implementation(self, implementation: list, logger: logging.Logger = None) -> str:
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
        logger.info(f"Generated implementation:\n{original_implementation}")
        # Extract the generated implementation using regex
        match = self.generated_implementation_regex.search(original_implementation)
        if match:
            implementation = match.group(1).strip()
        else:
            self.logger.warning("No generated implementation found in the response.")
            implementation = "sorry"
        return implementation

    
    def parse_proof(self, proof: list, logger: logging.Logger = None) -> str:
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
        logger.info(f"Generated proof:\n{original_proof}")
        # Extract the generated spec using regex
        match = self.generated_proof_regex.search(original_proof)
        if match:
            proof = match.group(1).strip()
        else:
            self.logger.warning("No generated proof found in the response.")
            proof = "sorry"
        helper_lemmas = self.generated_helper_lemmas_regex.search(original_proof)
        if helper_lemmas:
            helper_lemmas = helper_lemmas.group(1).strip()
            if helper_lemmas:
                self.helper_lemmas = helper_lemmas
        return proof
    

    def generate_implementation(self, timeout_in_ms = 60, logger = None) -> str:
        """
        Generate an implementation for the task using few-shot learning.
        """
        # Implement the logic to generate an implementation using few-shot learning
        logger = logger if logger else self.logger
        simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.impl_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.impl_prompt_settings.example_prompt_path,
            temperature=self.impl_model_settings.temperature,
            max_tokens_per_action=self.impl_prompt_settings.max_tokens_per_action,
            max_history_messages=self.impl_prompt_settings.max_history_messages,
            model_name=self.impl_model_settings.model_name,
            secret_filepath=self.impl_model_settings.secret_path,
            end_tokens=self.impl_prompt_settings.end_tokens,
            logger=logger
        )
        problem = self.problem_view.get_view(self.problem_id)
        prompt = "[NL DESCRIPTION]\n" \
        f"{problem.problem_spec_nl}\n" \
        "[SPECIFICATION]\n" \
        f"{problem.problem_spec_formal_ground_truth}\n" \
        "[IMPLEMENTATION SIGNATURE]\n" \
        f"{problem.implementation_signature}\n" \
        "[TEST CASES]\n" \
        f"{problem.test_cases_lean}"
        implementation = simple_prompter.run_prompt(prompt)
        parsed_implementation = self.parse_implementation(implementation, logger=logger)
        self.generated_implementation = parsed_implementation
        # Add the generated implementation to the problem view
        problem.implementation = parsed_implementation
        self.generated_impl_problem_view = problem
        return parsed_implementation

    def generate_implementation_correctness_proof(self, timeout_in_ms = 60, logger = None) -> str: # TODO: modify to use FewShotProverTool?
        assert self.generated_impl_problem_view is not None, "generated_impl_problem_view is None. Please generate the implementation first."
        logger = logger if logger else self.logger
        problem = self.problem_view.get_view(self.problem_id)
        problem.implementation = self.generated_impl_problem_view.implementation
        try:
            simple_prompter = SimplePrompter(
                main_sys_prompt_path=self.proof_prompt_settings.system_prompt_path,
                example_conv_prompt_path=self.proof_prompt_settings.example_prompt_path,
                temperature=self.proof_model_settings.temperature,
                max_tokens_per_action=self.proof_prompt_settings.max_tokens_per_action,
                max_history_messages=self.proof_prompt_settings.max_history_messages,
                model_name=self.proof_model_settings.model_name,
                secret_filepath=self.proof_model_settings.secret_path,
                end_tokens=self.proof_prompt_settings.end_tokens,
                logger=logger
            )
            prompt = "[NL DESCRIPTION]\n" \
            f"{problem.problem_spec_nl}\n" \
            "[SPECIFICATION]\n" \
            f"{problem.problem_spec_formal_ground_truth}\n" \
            "[IMPLEMENTATION]\n" \
            f"{problem.implementation}\n" \
            "[CORRECTNESS THEOREM]\n" \
            f"{problem.correctness_theorem}"
            proof = simple_prompter.run_prompt(prompt)
            proof = self.parse_proof(proof, logger=logger)
            if self.helper_lemmas is not None:
                # Put all the lemmas together
                problem.correctness_helper_lemmas.append(Lemma(statement=self.helper_lemmas, proof=""))
            problem.correctness_proof = proof
            formatted_problem, _ = format_problem_as_lean_with_line_ranges(problem)
            # Write the proof to a file
            report_dir = self.problem_view.report_dir
            os.makedirs(report_dir, exist_ok=True)
            base_filename = os.path.basename(self.file_path)[:-len(".lean")] + f"_problem_{self.problem_id}.lean"
            temporary_file_name = f"{os.path.join(report_dir, base_filename)}"
            with open(temporary_file_name, "w") as f:
                f.write(formatted_problem)
            # Writing the proof to the file
            self.logger.info(f"Writing the proof to {temporary_file_name}")
            self.generated_proof_problem_view = problem
            return proof
        finally:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
