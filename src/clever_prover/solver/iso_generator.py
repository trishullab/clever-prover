import logging
import time
import asyncio
import os
import copy
from collections import namedtuple
from clever_bench.task import ProblemViewTask
from clever_bench.lean_problem import Lemma, LeanProblemView, format_problem_as_lean_with_line_ranges
from clever_prover.tasks.spec_generation_task import SpecGenerationTask
from clever_prover.prompters.simple_prompter import SimplePrompter
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_prover.solver.tools.specification_planner_tool import SpecificationPlannerTool
from clever_prover.solver.tools.spec_generator_tool import SpecGeneratorTool
from clever_prover.solver.tools.proof_planner_tool import ProofPlannerTool
from clever_prover.solver.tools.few_shot_iso_prover_tool import FewShotIsoProverTool
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
    "isomorphism_proof_strategy",
])

class IsoGenerator(SpecGenerationTask):
    """
    Isomorphism generation task for CoPrA.
    """
    def __init__(self,
        problem_id: int,
        problem_view: ProblemViewTask,
        proof_dump_file_path: str,
        spec_prompt_settings: PromptSettings,
        spec_model_settings: ModelSettings,
        prover_prompt_settings: PromptSettings,
        prover_model_settings: ModelSettings,
        uses_copra_prover: bool,
        proof_planner_model_settings: ModelSettings = None,
        proof_planner_prompt_settings: PromptSettings = None,
        spec_planner_prompt_settings: PromptSettings = None,
        spec_planner_model_settings: ModelSettings = None,
        lemma_name="spec_isomorphism",
        num_spec_samples=5,
        num_proof_plan_samples=5,
        logger: logging.Logger = None):
        """
        Initialize the IsoGenerator with project path, file path, and lemma name.
        """
        super().__init__(problem_id=problem_id, problem_view=problem_view, lemma_name=lemma_name, logger=logger)
        self.spec_planner_prompt_settings = spec_planner_prompt_settings
        self.spec_planner_model_settings = spec_planner_model_settings
        if spec_planner_prompt_settings is None:
            assert spec_planner_model_settings is None, "If prompt settings are None, model settings should also be None."
        else:
            assert spec_planner_model_settings is not None, "If prompt settings are provided, model settings should also be provided."
        if proof_planner_prompt_settings is None:
            assert proof_planner_model_settings is None, "If prompt settings are None, model settings should also be None."
        else:
            assert proof_planner_model_settings is not None, "If prompt settings are provided, model settings should also be provided."
        self.proof_planner_prompt_settings = proof_planner_prompt_settings
        self.proof_planner_model_settings = proof_planner_model_settings
        self.spec_prompt_settings = spec_prompt_settings
        self.spec_model_settings = spec_model_settings
        self.prover_prompt_settings = prover_prompt_settings
        self.prover_model_settings = prover_model_settings
        self.num_spec_samples = num_spec_samples
        self.num_proof_plan_samples = num_proof_plan_samples
        self.proof_dump_file_path = proof_dump_file_path
        self.use_copra_prover = uses_copra_prover
        self.generated_spec = None
        self.helper_lemmas = None
        self.generated_proof = None
        self.spec_plan = None
    
    @property
    def use_spec_planner(self):
        return self.spec_planner_prompt_settings is not None and self.spec_planner_model_settings is not None

    @property
    def use_proof_planner(self):
        return self.proof_planner_prompt_settings is not None and self.proof_planner_model_settings is not None
    
    @property
    def use_copra(self):
        return self.use_copra_prover
    
    def generate_specification(self, timeout_in_ms = 60, logger = None):
        logger = logger if logger else self.logger
        spec_stable = False
        spec_sample_count = 0
        is_time_elapsed = False
        start_time = time.time()
        elapsed_time = 0
        time_remaining_in_ms = timeout_in_ms
        while not is_time_elapsed and not spec_stable and spec_sample_count < self.num_spec_samples:
            logger.info(f"(Try #{spec_sample_count + 1}) Generating isomorphism spec for problem {self.problem_id}...")
            problem = self.problem_view.get_view(self.problem_id)
            # Ensure no accidental leakage
            problem.problem_spec_formal_generated += "\n"
            problem.isomorphism_helper_lemmas.clear()
            problem.isomorphism_proof = None
            lean_code = self._generate_spec(problem=problem, logger=logger)
            problem.problem_spec_formal_generated += lean_code
            validation_result =  self._submit(problem, time_remaining_in_ms)
            spec_stable = validation_result.compilation_ok
            elapsed_time = time.time() - start_time
            time_remaining_in_ms = timeout_in_ms - (elapsed_time * 1000)
            is_time_elapsed = time_remaining_in_ms <= 0
            spec_sample_count += 1
            if spec_stable:
                logger.info("Isomorphism spec generation succeeded.")
            else:
                logger.info("Isomorphism spec generation failed.")
        self.generated_spec = lean_code
        self.generated_spec_problem_view = problem
        return lean_code

    def generate_spec_isomorphism_proof(self, timeout_in_ms = 60, logger = None):
        logger = logger if logger else self.logger
        proof = "by sorry"
        proof_found = False
        proof_sample_count = 0
        is_time_elapsed = False
        start_time = time.time()
        elapsed_time = 0
        time_remaining_in_ms = timeout_in_ms
        plan_generation_failed = False
        while not is_time_elapsed and not proof_found and proof_sample_count < self.num_proof_plan_samples:
            logger.info(f"(Try #{proof_sample_count + 1}) Generating proof for problem {self.problem_id}...")
            problem = self.problem_view.get_view(self.problem_id)
            # Ensure no accidental leakage
            problem.problem_spec_formal_generated += "\n"
            problem.isomorphism_helper_lemmas.clear()
            problem.isomorphism_proof = None
            if self.generated_spec is None:
                raise ValueError("Isomorphism must be generated before generating the proof.")
            problem.problem_spec_formal_generated += self.generated_spec
            if self.use_proof_planner:
                proof_plan = self._generate_proof_plan(problem=problem, logger=logger)
                lemma_plans : list[LemmaPlan] = proof_plan.lemma_plans
                proven_lemmas : list[Lemma] = []
                for lemma_plan in lemma_plans:
                    theorem_statement = lemma_plan.lemma
                    problem.isomorphism_helper_lemmas.append(
                        Lemma(statement=theorem_statement, proof="by sorry"))
                if len(lemma_plans) > 0:
                    validation_result = self._submit(problem, time_remaining_in_ms)
                    if not validation_result.compilation_ok:
                        plan_generation_failed = True
                        self.logger.info("Lemmas failed to compile.")
                    else:
                        plan_generation_failed = False
                        self.logger.info("Lemmas compiled successfully.")
                else:
                    plan_generation_failed = False
                    self.logger.info("No helper lemmas generated.")
            else:
                proof_plan = None
                lemma_plans = []
                proven_lemmas = []
                plan_generation_failed = False
            if not plan_generation_failed:
                if len(lemma_plans) > 0:
                    proven_lemmas, proven_lemmas_str, time_remaining_in_ms = self._generate_proof_for_all_lemmas(
                        lemma_plans=lemma_plans,
                        problem=problem,
                        time_remaining_in_ms=time_remaining_in_ms,
                        logger=logger)
                else:
                    proven_lemmas = []
                    proven_lemmas_str = ""
                problem.isomorphism_helper_lemmas.clear()
                for proven_lemma in proven_lemmas:
                    problem.isomorphism_helper_lemmas.append(proven_lemma)
                if proof_plan is not None:
                    full_proof_strategy = proof_plan.isomorphism_proof_strategy + proven_lemmas_str
                else:
                    full_proof_strategy = ""
                proof, proof_found, time_remaining_in_ms = self._generate_proof(
                    problem=problem,
                    theorem_description=problem.problem_spec_nl,
                    proof_strategy=full_proof_strategy,
                    start_time=start_time,
                    time_remaining_in_ms=time_remaining_in_ms,
                    theorem_name=self.lemma_name,
                    logger=logger)
                problem.isomorphism_proof = proof
            else:
                proven_lemmas = []
                proven_lemmas_str = ""
            elapsed_time = time.time() - start_time
            time_remaining_in_ms = timeout_in_ms - (elapsed_time * 1000)
            is_time_elapsed = time_remaining_in_ms <= 0
            proof_sample_count += 1
        problem.isomorphism_proof = proof
        self.generated_proof_problem_view = problem
        full_lean_code, _ = format_problem_as_lean_with_line_ranges(problem)
        report_dir = self.problem_view.report_dir
        file_name = f"iso_gen_{self.problem_id}.lean"
        file_path = os.path.join(report_dir, file_name)
        with open(file_path, "w") as f:
            f.write(full_lean_code)
        return proof

    def _generate_spec(self, problem: LeanProblemView, logger: logging.Logger = None):
        logger = logger if logger else self.logger
        if self.use_spec_planner:
            isomorphism_plan = self._generate_spec_plan(problem=problem, logger=logger)
            self.spec_plan = isomorphism_plan
        iso_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.spec_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.spec_prompt_settings.example_prompt_path,
            temperature=self.spec_model_settings.temperature,
            max_tokens_per_action=self.spec_prompt_settings.max_tokens_per_action,
            max_history_messages=self.spec_prompt_settings.max_history_messages,
            model_name=self.spec_model_settings.model_name,
            secret_filepath=self.spec_model_settings.secret_path,
            end_tokens=self.spec_prompt_settings.end_tokens,
            logger=logger)
        specification_generator = SpecGeneratorTool(
            simple_prompter=iso_simple_prompter,
            logger=logger
        )
        lean_code = specification_generator.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            spec_signature=problem.problem_spec_formal_generated,
            spec_plan=self.spec_plan
        )
        specification_generator.reset()
        lean_code = lean_code.strip()
        return lean_code

    def _generate_spec_plan(self, problem: LeanProblemView, logger: logging.Logger = None):
        logger = logger if logger else self.logger
        impl_planner_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.spec_planner_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.spec_planner_prompt_settings.example_prompt_path,
            temperature=self.spec_planner_model_settings.temperature,
            max_tokens_per_action=self.spec_planner_prompt_settings.max_tokens_per_action,
            max_history_messages=self.spec_planner_prompt_settings.max_history_messages,
            model_name=self.spec_planner_model_settings.model_name,
            secret_filepath=self.spec_planner_model_settings.secret_path,
            end_tokens=self.spec_planner_prompt_settings.end_tokens,
            logger=logger
        )
        impl_planner = SpecificationPlannerTool(
            simple_prompter=impl_planner_simple_prompter,
            logger=logger
        )
        implementation_plan = impl_planner.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            spec_signature=problem.implementation_signature,
            test_cases=problem.test_cases_lean
        )
        impl_planner.reset()
        return implementation_plan

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
        raw_proof_plan, lemmas, lemma_plans, isomorphism_proof_plan = proof_planner.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            implementation_signature=problem.implementation_signature,
            implementation=problem.implementation,
            correctness_definition=problem.isomorphism_theorem
        )
        proof_planner.reset()
        lemma_plan_objs = []
        for lemma, lemma_plan in zip(lemmas, lemma_plans):
            try:
                lemma_name = self._get_lemma_name(lemma)
            except ValueError:
                self.logger.warning(f"Invalid lemma name format: {lemma}. Skipping this lemma.")
                continue
            lemma_plan_objs.append(LemmaPlan(
                lemma_name=lemma_name,
                lemma=lemma,
                lemma_proof_strategy=lemma_plan))
        proof_plan = ProofPlan(
            raw_proof_plan=raw_proof_plan,
            lemma_plans=lemma_plan_objs,
            isomorphism_proof_strategy=isomorphism_proof_plan
        )
        return proof_plan
    
    def _generate_proof_for_all_lemmas(self, 
        lemma_plans: list[LemmaPlan], 
        problem: LeanProblemView, 
        time_remaining_in_ms: int, 
        logger: logging.Logger = None) -> tuple[list[Lemma], str, int]:
        logger = logger if logger else self.logger
        proven_lemmas_str = ""
        proven_lemmas = []
        start_time = time.time()
        is_time_elapsed = False
        for lemma_plan in lemma_plans:
            full_proof_strategy = lemma_plan.lemma_proof_strategy + proven_lemmas_str
            proof, proof_found, time_remaining_in_ms = self._generate_proof(
                problem=problem,
                theorem_description=lemma_plan.lemma,
                proof_strategy=full_proof_strategy,
                start_time=start_time,
                time_remaining_in_ms=time_remaining_in_ms,
                theorem_name=lemma_plan.lemma_name,
                logger=logger
            )
            is_time_elapsed = time_remaining_in_ms <= 0
            if proof_found:
                theorem_statement = lemma_plan.lemma
                proven_lemmas.append(Lemma(statement=theorem_statement, proof=proof))
                if len(proven_lemmas) == 1:
                    proven_lemmas_str = "\n\nThroughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:"
                    proven_lemmas_str += "\n[HELPER LEMMAS]"
                proven_lemmas_str += ("\n[HELPER LEMMA]\n" + theorem_statement)
            if is_time_elapsed:
                self.logger.info("Time elapsed while generating proof for lemma.")
                break
        return proven_lemmas, proven_lemmas_str, time_remaining_in_ms

    def _generate_proof(
            self,
            problem: LeanProblemView,
            theorem_description: str,
            proof_strategy: str,
            start_time: float,
            time_remaining_in_ms: int,
            theorem_name: str,
            logger: logging.Logger = None) -> tuple[str, bool, int]:
        if len(proof_strategy.strip()) == 0:
            proof_strategy = None
        try:
            if self.use_copra:
                proof_result = self._generate_proof_via_copra(
                    problem=problem,
                    theorem_name=theorem_name,
                    lemma_description=theorem_description,
                    lemma_proof_strategy=proof_strategy,
                    proof_dump_file_path=self.proof_dump_file_path,
                    timeout_in_ms=time_remaining_in_ms,
                    logger=logger
                )
                proof_success = proof_result.proof_found
                proof_steps = [step for proof_step in proof_result.proof_steps for step in proof_step.proof_steps]
                proof = "by\n" + "\n".join(proof_steps)
            else:
                proof, proof_success = self._generate_few_shot_proof(
                    problem=problem,
                    theorem_name=theorem_name,
                    lemma_proof_strategy=proof_strategy,
                    proof_dump_file_path=self.proof_dump_file_path,
                    timeout_in_ms=time_remaining_in_ms,
                    logger=logger
                )
        except Exception as e:
            self.logger.exception(e)
            proof = "by sorry"
            proof_success = False
        elapsed_time = time.time() - start_time
        time_remaining_in_ms = time_remaining_in_ms - (elapsed_time * 1000)
        return proof, proof_success, time_remaining_in_ms

    def _generate_proof_via_copra(
        self,
        problem: LeanProblemView,
        theorem_name: str,
        lemma_description: str,
        lemma_proof_strategy: str,
        proof_dump_file_path: str,
        timeout_in_ms: int = 60,
        logger: logging.Logger = None) -> ProofSearchResult:
        logger = logger if logger else self.logger
        file_path = self.file_path
        full_lean_code, _ = format_problem_as_lean_with_line_ranges(problem)
        with open(file_path, "w") as f:
            f.write(full_lean_code)
        if lemma_description is None:
            lemma_description = problem.problem_spec_nl
        proof_search_result = get_proof_via_copra(
            project_path=self.project_path,
            file_path=file_path,
            lemma_name=theorem_name,
            informal_problem=lemma_description,
            informal_hints=lemma_proof_strategy,
            timeout_in_ms=timeout_in_ms,
            proof_dump_file_path=proof_dump_file_path,
            system_prompt=self.prover_prompt_settings.system_prompt_path,
            example_prompt=self.prover_prompt_settings.example_prompt_path,
            model_name=self.prover_model_settings.model_name,
            temperature=self.prover_model_settings.temperature,
            max_history_messages=self.prover_prompt_settings.max_history_messages,
            secret_filepath=self.prover_model_settings.secret_path,
            max_tokens_per_action=self.prover_prompt_settings.max_tokens_per_action,
            logger=self.logger
        )
        return proof_search_result
    
    def _generate_few_shot_proof(
        self,
        problem: LeanProblemView,
        theorem_name: str,
        lemma_proof_strategy: str,
        proof_dump_file_path: str,
        timeout_in_ms: int = 60,
        logger: logging.Logger = None) -> str:
        few_shot_prover_simple_prompter = SimplePrompter(
            main_sys_prompt_path=self.prover_prompt_settings.system_prompt_path,
            example_conv_prompt_path=self.prover_prompt_settings.example_prompt_path,
            temperature=self.prover_model_settings.temperature,
            max_tokens_per_action=self.prover_prompt_settings.max_tokens_per_action,
            max_history_messages=self.prover_prompt_settings.max_history_messages,
            model_name=self.prover_model_settings.model_name,
            secret_filepath=self.prover_model_settings.secret_path,
            end_tokens=self.prover_prompt_settings.end_tokens,
            logger=logger
        )
        few_shot_prover = FewShotIsoProverTool(
            simple_prompter=few_shot_prover_simple_prompter,
            logger=logger
        )
        # Find the lemma using lemma_name in isomorphism_helper_lemmas
        lemma_statement = None
        helper_lemma_idx = None
        for idx, lemma in enumerate(problem.isomorphism_helper_lemmas):
            lemma_name = self._get_lemma_name(lemma.statement)
            if lemma_name == theorem_name:
                lemma_statement = lemma.statement
                helper_lemma_idx = idx
                break
        if lemma_statement is None:
            lemma_statement = problem.isomorphism_theorem
        proof = few_shot_prover.solve_intermediate(
            problem_statement=problem.problem_spec_nl,
            problem_spec=problem.problem_spec_formal_ground_truth,
            generated_spec=problem.problem_spec_formal_generated,
            theorem_statement=lemma_statement,
            proof_plan=lemma_proof_strategy
        )
        problem_view_copy = copy.deepcopy(problem)
        if helper_lemma_idx is not None:
            problem_view_copy.isomorphism_helper_lemmas[helper_lemma_idx].proof = proof 
            for idx, lemma in enumerate(problem_view_copy.isomorphism_helper_lemmas):
                if idx != helper_lemma_idx:
                    problem_view_copy.isomorphism_helper_lemmas[idx].proof = "\nby sorry"
            validation_result = self._submit(problem_view_copy, timeout_in_ms)
            proof_found = validation_result.compilation_ok
        else:
            problem_view_copy.isomorphism_proof = proof
            validation_result = self._submit(problem_view_copy, timeout_in_ms)
            proof_found = validation_result.compilation_ok and validation_result.isomorphism_ok
        return proof, proof_found

    def _submit(self, problem: LeanProblemView, time_remaining_in_ms: int):
        validation_result = asyncio.run(
            self.problem_view.submit_async(
                problem,
                timeout_in_ms=time_remaining_in_ms))
        return validation_result

    def _get_lemma_name(self, lemma: str):
            match = Lean4SyncExecutor.theorem_name_match.match(lemma)
            if match:
                lemma_name = match.group(4).strip()
                return lemma_name
            else:
                raise ValueError(f"Invalid lemma name format: {lemma}. Expected format: 'theorem <name> : <type>'")