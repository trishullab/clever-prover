import logging
import time
import asyncio
import os
from collections import namedtuple
from clever_bench.task import ProblemViewTask
from clever_bench.lean_problem import Lemma, LeanProblemView, format_problem_as_lean_with_line_ranges
from clever_prover.tasks.implementation_generation_task import ImplementationGenerationTask
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_prover.solver.tools.implementation_planner_tool import ImplementationPlannerTool
from clever_prover.solver.tools.implementer_tool import ImplementerTool
from clever_prover.solver.tools.proof_planner_tool import ProofPlannerTool
from clever_prover.utils.copra import get_proof_via_copra, ProofSearchResult
from itp_interface.tools.lean4_sync_executor import Lean4SyncExecutor


LemmaPlan = namedtuple("LemmaPlan",
[
    "lemma_name",
    "lemma",
    "lemma_proof_strategy"
])

ProofPlan = namedtuple("ProofPlan",
[
    "raw_proof_plan",
    "lemma_plans",
    "correctness_proof_strategy",
])

class PlanningCopraImplGenerator(ImplementationGenerationTask):
    """
    Implementation generation task for CoPrA.
    """
    def __init__(self,
        problem_id: int,
        problem_view: ProblemViewTask,
        impl_planner_prompt_settings: PromptSettings,
        impl_planner_model_settings: ModelSettings,
        impl_prompt_settings: PromptSettings,
        impl_model_settings: ModelSettings,
        proof_planner_prompt_settings: PromptSettings,
        proof_planner_model_settings: ModelSettings,
        copra_prompt_settings: PromptSettings,
        copra_model_settings: ModelSettings,
        proof_dump_file_path: str,
        lemma_name="correctness",
        num_implementation_plan_samples=5,
        num_proof_plan_samples=5,
        logger: logging.Logger = None):
        """
        Initialize the PlanningCopraImplGenerator with project path, file path, and lemma name.
        """
        super().__init__(problem_id=problem_id, problem_view=problem_view, lemma_name=lemma_name, logger=logger)
        self.impl_planner_prompt_settings = impl_planner_prompt_settings
        self.impl_planner_model_settings = impl_planner_model_settings
        self.impl_prompt_settings = impl_prompt_settings
        self.impl_model_settings = impl_model_settings
        self.proof_planner_prompt_settings = proof_planner_prompt_settings
        self.proof_planner_model_settings = proof_planner_model_settings
        self.copra_prompt_settings = copra_prompt_settings
        self.copra_model_settings = copra_model_settings
        self.num_implementation_plan_samples = num_implementation_plan_samples
        self.num_proof_plan_samples = num_proof_plan_samples
        self.proof_dump_file_path = proof_dump_file_path
        self.generated_implementation = None
        self.helper_lemmas = None
        self.generated_proof = None
        self.implementation_plan = None
        self.proof_plan = None
    
    def generate_implementation(self, timeout_in_ms = 60, logger = None):
        implementation_stable = False
        implementation_sample_count = 0
        is_time_elapsed = False
        start_time = time.time()
        elapsed_time = 0
        time_remaining_in_ms = timeout_in_ms
        while not is_time_elapsed and not implementation_stable and implementation_sample_count < self.num_implementation_plan_samples:
            problem = self.problem_view.get_view(self.problem_id)
            # Ensure no accidental leakage
            problem.implementation = None
            problem.correctness_helper_lemmas.clear()
            problem.correctness_proof = None
            implementation_plan = self._generate_impl_plan(problem=problem, logger=logger)
            self.implementation_plan = implementation_plan
            lean_code = self._generate_impl(problem=problem, logger=logger)
            problem.implementation = lean_code
            validation_result = asyncio.run(
                self.problem_view.submit_async(
                    problem,
                    timeout_in_ms=time_remaining_in_ms))
            implementation_stable = validation_result.compilation_ok
            elapsed_time = time.time() - start_time
            time_remaining_in_ms = timeout_in_ms - (elapsed_time * 1000)
            is_time_elapsed = time_remaining_in_ms <= 0
            implementation_sample_count += 1
        problem.implementation = lean_code
        self.generated_implementation = lean_code
        self.generated_impl_problem_view = problem
        return lean_code

    def generate_implementation_correctness_proof(self, timeout_in_ms = 60, logger = None):
        proof_found = False
        proof_plan = None
        proof_sample_count = 0
        is_time_elapsed = False
        start_time = time.time()
        elapsed_time = 0
        time_remaining_in_ms = timeout_in_ms
        while not is_time_elapsed and not proof_found and proof_sample_count < self.num_proof_plan_samples:
            problem = self.problem_view.get_view(self.problem_id)
            # Ensure no accidental leakage
            problem.implementation = None
            problem.correctness_helper_lemmas.clear()
            problem.correctness_proof = None
            if self.generated_implementation is None:
                raise ValueError("Implementation must be generated before generating the proof.")
            problem.implementation = self.generated_implementation
            proof_plan = self._generate_proof_plan(problem=problem, logger=logger)
            self.proof_plan = proof_plan
            lemma_plans : list[LemmaPlan] = proof_plan.lemma_plans
            proven_lemmas : list[Lemma] = []
            # TODO: check compilation; continue if fails, make sure variables at end are updated
            for lemma_plan in lemma_plans:
                theorem_statement = lemma_plan.lemma
                problem.correctness_helper_lemmas.append(
                    Lemma(statement=theorem_statement, proof="by sorry"))
                full_proof_strategy = lemma_plan.lemma_proof_strategy
                # TODO: add each lemma only once
                if proven_lemmas:
                    full_proof_strategy += "\n\nThroughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:"
                    full_proof_strategy += "\n[HELPER LEMMAS]"
                for proven_lemma in proven_lemmas:
                    full_proof_strategy += ("\n[HELPER LEMMA]\n" + proven_lemma.statement)
                proof_result = self._generate_proof(
                    problem=problem,
                    theorem_name=lemma_plan.lemma_name,
                    lemma_proof_strategy=full_proof_strategy,
                    proof_dump_file_path=self.proof_dump_file_path,
                    timeout_in_ms=time_remaining_in_ms,
                    logger=logger
                )
                if proof_result.proof_found:
                    proof_steps = [step for proof_step in proof_result.proof_steps for step in proof_step.proof_steps]
                    proof = "\n".join(proof_steps)
                    proven_lemmas.append(Lemma(statement=theorem_statement, proof=proof))
            problem.correctness_helper_lemmas.clear()
            full_proof_strategy = proof_plan.correctness_proof_strategy
            if proven_lemmas:
                full_proof_strategy += "\n\nThroughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:"
                full_proof_strategy += "\n[HELPER LEMMAS]"
            for proven_lemma in proven_lemmas:
                problem.correctness_helper_lemmas.append(proven_lemma)
                full_proof_strategy += ("\n[HELPER LEMMA]\n" + proven_lemma.statement)
            # TODO: need to add lemmas to proof file before we can prove them, else error
            proof_result = self._generate_proof(
                problem=problem,
                theorem_name=self.lemma_name,
                lemma_proof_strategy=full_proof_strategy,
                proof_dump_file_path=self.proof_dump_file_path,
                timeout_in_ms=time_remaining_in_ms,
                logger=logger)
            if proof_result.proof_found:
                proof_steps = [step for proof_step in proof_result.proof_steps for step in proof_step.proof_steps]
                proof = "by\n" + "\n".join(proof_steps)
                problem.correctness_proof = proof
                proof_found = True
            else:
                proof = "sorry"
            elapsed_time = time.time() - start_time
            time_remaining_in_ms = timeout_in_ms - (elapsed_time * 1000)
            is_time_elapsed = time_remaining_in_ms <= 0
            proof_sample_count += 1
        problem.correctness_proof = proof
        self.generated_proof_problem_view = problem
        full_lean_code, _ = format_problem_as_lean_with_line_ranges(problem)
        report_dir = self.problem_view.report_dir
        file_name = f"impl_gen_{self.problem_id}.lean"
        file_path = os.path.join(report_dir, file_name)
        with open(file_path, "w") as f:
            f.write(full_lean_code)
        return proof

    def _generate_impl_plan(self, problem: LeanProblemView, logger: logging.Logger = None):
        logger = logger if logger else self.logger
        impl_planner_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.impl_planner_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.impl_planner_prompt_settings.example_prompt_path,
            temperature=self.impl_planner_model_settings.temperature,
            max_tokens_per_action=self.impl_planner_prompt_settings.max_tokens_per_action,
            max_history_messages=self.impl_planner_prompt_settings.max_history_messages,
            model_name=self.impl_planner_model_settings.model_name,
            secret_filepath=self.impl_planner_model_settings.secret_path,
            end_tokens=self.impl_planner_prompt_settings.end_tokens,
            logger=logger
        )
        impl_planner = ImplementationPlannerTool(
            simple_prompter=impl_planner_simple_prompter,
            logger=logger
        )
        implementation_plan = impl_planner.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            implementation_signature=problem.implementation_signature,
            test_cases=problem.test_cases_lean
        )
        return implementation_plan
    
    def _generate_impl(self, problem: LeanProblemView, logger: logging.Logger = None):
        logger = logger if logger else self.logger
        impl_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.impl_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.impl_prompt_settings.example_prompt_path,
            temperature=self.impl_model_settings.temperature,
            max_tokens_per_action=self.impl_prompt_settings.max_tokens_per_action,
            max_history_messages=self.impl_prompt_settings.max_history_messages,
            model_name=self.impl_model_settings.model_name,
            secret_filepath=self.impl_model_settings.secret_path,
            end_tokens=self.impl_prompt_settings.end_tokens,
            logger=logger)
        implementation_generator = ImplementerTool(
            simple_prompter=impl_simple_prompter,
            logger=logger
        )
        lean_code = implementation_generator.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            implementation_signature=problem.implementation_signature,
            test_cases=problem.test_cases_lean,
            implementation_plan=self.implementation_plan
        )
        lean_code = lean_code.strip()
        return lean_code

    def _generate_proof_plan(self, problem: LeanProblemView, logger: logging.Logger = None):
        proof_planner_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.proof_planner_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.proof_planner_prompt_settings.example_prompt_path,
            temperature=self.proof_planner_model_settings.temperature,
            max_tokens_per_action=self.proof_planner_prompt_settings.max_tokens_per_action,
            max_history_messages=self.proof_planner_prompt_settings.max_history_messages,
            model_name=self.proof_planner_model_settings.model_name,
            secret_filepath=self.proof_planner_model_settings.secret_path,
            end_tokens=self.proof_planner_prompt_settings.end_tokens,
            logger=logger
        )
        proof_planner = ProofPlannerTool(
            simple_prompter=proof_planner_simple_prompter,
            logger=logger
        )
        raw_proof_plan, lemmas, lemma_plans, correctness_plan = proof_planner.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            implementation_signature=problem.implementation_signature,
            implementation=problem.implementation,
            correctness_definition=problem.correctness_theorem
        )
        lemma_plan_objs = []
        for lemma, lemma_plan in zip(lemmas, lemma_plans):
            match = Lean4SyncExecutor.theorem_name_match.match(lemma)
            if match:
                lemma_name = match.group(4).strip()
                lemma_plan_objs.append(LemmaPlan(
                    lemma_name=lemma_name,
                    lemma=lemma,
                    lemma_proof_strategy=lemma_plan))
        proof_plan = ProofPlan(
            raw_proof_plan=raw_proof_plan,
            lemma_plans=lemma_plan_objs,
            correctness_proof_strategy=correctness_plan
        )
        return proof_plan
    
    def _generate_proof(
        self,
        problem: LeanProblemView,
        theorem_name: str,
        lemma_proof_strategy: str,
        proof_dump_file_path: str,
        timeout_in_ms: int = 60,
        logger: logging.Logger = None) -> ProofSearchResult:
        logger = logger if logger else self.logger
        file_path = self.file_path
        full_lean_code, _ = format_problem_as_lean_with_line_ranges(problem)
        with open(file_path, "w") as f:
            f.write(full_lean_code)
        proof_search_result = get_proof_via_copra(
            project_path=self.project_path,
            file_path=file_path,
            lemma_name=theorem_name,
            informal_problem=problem.problem_spec_nl,
            informal_hints=lemma_proof_strategy,
            timeout_in_ms=timeout_in_ms,
            proof_dump_file_path=proof_dump_file_path,
            system_prompt=self.copra_prompt_settings.system_prompt_path,
            example_prompt=self.copra_prompt_settings.example_prompt_path,
            model_name=self.copra_model_settings.model_name,
            temperature=self.copra_model_settings.temperature,
            max_history_messages=self.copra_prompt_settings.max_history_messages,
            secret_filepath=self.copra_model_settings.secret_path,
            max_tokens_per_action=self.copra_prompt_settings.max_tokens_per_action,
            logger=self.logger
        )
        return proof_search_result