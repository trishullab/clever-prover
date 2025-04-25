import logging
import os
import re
from clever_prover.tasks.spec_generation_task import SpecGenerationTask
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_bench.task import ProblemViewTask
from clever_bench.lean_problem import format_problem_as_lean_with_line_ranges, Lemma
from clever_prover.prompters.simple_prompter import SimplePrompter

class FewShotSpecGenerationTask(SpecGenerationTask):
    generated_spec_regex = re.compile(r"\[GENERATED SPECIFICATION\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    generated_helper_regex = re.compile(r"\[HELPER DEFINITIONS\]\s*([\s\S]*?)\s*\[END DEFINITIONS\]", re.MULTILINE)
    generated_helper_lemmas_regex = re.compile(r"\[HELPER LEMMAS\]\s*([\s\S]*?)\s*\[END LEMMAS\]", re.MULTILINE)
    generated_proof_regex = re.compile(r"\[PROOF\]\s*([\s\S]*?)\s*\[END\]", re.MULTILINE)
    def __init__(self, 
        problem_id: int,
        problem_view: ProblemViewTask,
        spec_prompt_settings: PromptSettings,
        spec_model_settings: ModelSettings,
        proof_prompt_settings: PromptSettings,
        proof_model_settings: ModelSettings,
        lemma_name="spec_isomorphism",
        logger: logging.Logger = None):
        """
        Initialize the FewShotSpecGenerationTask with project path, file path, and lemma name.
        """
        super().__init__(problem_id=problem_id, problem_view=problem_view, lemma_name=lemma_name, logger=logger)
        self.proof_prompt_settings = proof_prompt_settings
        self.proof_model_settings = proof_model_settings
        self.spec_prompt_settings = spec_prompt_settings
        self.spec_model_settings = spec_model_settings
        self.generated_spec = None
        self.helper_definitions = None
        self.helper_lemmas = None
        self.generated_proof = None

    def parse_spec(self, spec: list, logger: logging.Logger = None) -> str:
        """
        Parse the specification string into a list of lemmas.
        """
        # Implement the logic to parse the specification string
        # For example, split by newlines and filter out empty lines
        assert isinstance(spec, list), "spec should be a list"
        assert len(spec) == 1, "spec should be a single string"
        assert isinstance(spec[0], dict), "spec should be a list of dicts"
        assert 'content' in spec[0], "spec should contain 'content' key"
        assert isinstance(spec[0]['content'], str), "spec content should be a string"
        original_spec: str = spec[0]['content'].strip()
        if not original_spec.endswith("[END]"):
            original_spec += "\n[END]"
        logger = logger if logger else self.logger
        logger.info(f"Generated spec:\n{original_spec}")
        # Extract the generated spec using regex
        match = self.generated_spec_regex.search(original_spec)
        if match:
            spec = match.group(1).strip()
        else:
            self.logger.warning("No generated spec found in the response.")
            spec = "sorry"
        helper_definitions = self.generated_helper_regex.search(original_spec)
        if helper_definitions:
            helper_definitions = helper_definitions.group(1).strip()
            if helper_definitions:
                self.helper_definitions = helper_definitions                
        return spec

    
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
    

    def generate_specification(self, timeout_in_ms = 60, logger = None) -> str:
        """
        Generate a specification for the task using few-shot learning.
        """
        # Implement the logic to generate a specification using few-shot learning
        logger = logger if logger else self.logger
        simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.spec_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.spec_prompt_settings.example_prompt_path,
            temperature=self.spec_model_settings.temperature,
            max_tokens_per_action=self.spec_prompt_settings.max_tokens_per_action,
            max_history_messages=self.spec_prompt_settings.max_history_messages,
            model_name=self.spec_model_settings.model_name,
            secret_filepath=self.spec_model_settings.secret_path,
            end_tokens=self.spec_prompt_settings.end_tokens,
            logger=logger
        )
        problem = self.problem_view.get_view(self.problem_id)
        prompt = "[NL DESCRIPTION]\n" \
        f"{problem.problem_spec_nl}\n" \
        "[SPECIFICATION SIGNATURE]\n" \
        f"{problem.problem_spec_formal_generated}"
        spec = simple_prompter.run_prompt(prompt)
        # TODO: Add Helper Definitions
        parsed_spec = self.parse_spec(spec, logger=logger)
        self.generated_spec = parsed_spec
        all_helper_definitions = self.helper_definitions
        if all_helper_definitions is not None:
            problem.problem_spec_formal_generated = all_helper_definitions + "\n" + problem.problem_spec_formal_generated
        # Add the generated spec to the problem view
        problem.problem_spec_formal_generated += ("\n" + parsed_spec)
        self.generated_spec_problem_view = problem
        return parsed_spec

    def generate_spec_isomorphism_proof(self, timeout_in_ms = 60, logger = None) -> str:
        assert self.generated_spec_problem_view is not None, "generated_spec_problem_view is None. Please generate the specification first."
        logger = logger if logger else self.logger
        problem = self.problem_view.get_view(self.problem_id)
        problem.problem_spec_formal_generated = self.generated_spec_problem_view.problem_spec_formal_generated
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
            "[GROUND TRUTH SPECIFICATION]\n" \
            f"{problem.problem_spec_formal_ground_truth}\n" \
            "[GENERATED SPECIFICATION]\n" \
            f"{problem.problem_spec_formal_generated}\n" \
            "[ISOMORPHISM THEOREM]\n" \
            f"{problem.isomorphism_theorem}"
            proof = simple_prompter.run_prompt(prompt)
            proof = self.parse_proof(proof, logger=logger)
            if self.helper_lemmas is not None:
                # Put all the lemmas together
                problem.isomorphism_helper_lemmas.append(Lemma(statement=self.helper_lemmas, proof=""))
            problem.isomorphism_proof = proof
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
