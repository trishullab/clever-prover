import logging
import typing
import time
import tempfile
import subprocess
from sympy import *
from clever_bench.task import ProblemViewTask
from clever_prover.solver.abs_solver_and_tool import Solver, Tool
from clever_prover.solver.tools.implementation_planner_tool import ImplementationPlannerTool
from clever_prover.solver.tools.implementer_tool import ImplementerTool
from clever_prover.solver.tools.proof_planner_tool import ProofPlannerTool
from enum import Enum

class CoordinationSolverStrategy(Enum):
    PLANNER_IMPLEMENTER_PLANNER_PROVER_CHAIN = "planner_implementer_planner_prover_chain"

    def __str__(self):
        return self.value

class CoordinationSolver(Solver):

    def __init__(self,
        tools: typing.Dict[str, Tool],
        strategy: CoordinationSolverStrategy,
        logger: logging.Logger = None,
        coordinator_history_logger: logging.Logger = None,
        **coordination_kwargs):
        self.logger = logger
        self.coordinator_history_logger = coordinator_history_logger
        self.tools = tools
        self.strategy = strategy
        self.coordination_kwargs = coordination_kwargs
        self.history_buffer = []
        self._init_hyperparameters()
    
    def _init_hyperparameters(self):
        self.num_code_gens = self.coordination_kwargs.get("num_code_gens", 1)
        self.num_plans = self.coordination_kwargs.get("num_plans", 1)
        self.code_timeout_in_secs = self.coordination_kwargs.get("code_timeout_in_secs", 2*60) # 2 minutes default
        self.problem_timeout_in_secs = self.coordination_kwargs.get("problem_timeout_in_secs", 20*60) # 20 minutes default
        self.num_attempts = self.coordination_kwargs.get("num_attempts", 5)
        self.picker_optional = self.coordination_kwargs.get("picker_optional", False)
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        for tool in self.tools.values():
            tool.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for tool in self.tools.values():
            tool.__exit__(exc_type, exc_val, exc_tb)

    def reset(self):
        for tool in self.tools.values():
            tool.reset()
        self.history_buffer.clear()
    
    def _convert_float_to_rational(self, float_num: float) -> Rational:
        return Rational(float_num).limit_denominator()

    def _run_simplify(self, output, context):
        context["simp_output"] = simplify(output)
    
    def _log_and_add_to_history_buffer(self, message):
        self.logger.info(message)
        self.history_buffer.append(message)


    def _check_implementation(self, implementation, test_cases) -> bool: # TODO: maybe add error feedback later
        temp_lean_file_text = f"""import Imports.AllImports

{implementation}

{test_cases}
"""
        
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".lean") as temp_lean_file:
            temp_lean_file.write(temp_lean_file_text)
            temp_lean_file.flush()

            result = subprocess.run(["lake", "env", "lean", temp_lean_file.name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd="../../../clever/src/lean4/", text=True)

        self.logger.info(f"Check implementation output:\n{result.stdout.strip()}")
        
        return (result.returncode == 0)

    def _planner_implementer_planner_prover_chain(self, problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str, correctness_definition: str, time_allowed: int):
        implementation_planner: ImplementationPlannerTool = self.tools["implementation_planner"]
        implementer: ImplementerTool = self.tools["implementer"]
        proof_planner: ProofPlannerTool = self.tools["proof_planner"]

        NUM_IMPLEMENTATION_SAMPLES = 10
        implementation_plan = "N/A"
        implementation = implementation_signature
        implementation_passes = False
        for i in range(NUM_IMPLEMENTATION_SAMPLES): # TODO: do this in parallel instead?
            self.logger.info(f"Sampling implementation planner and implementer: {i+1} of {NUM_IMPLEMENTATION_SAMPLES}")

            try:
                implementation_plan = implementation_planner.solve_intermediate(problem_statement, problem_spec, implementation_signature, test_cases)
                self.logger.info(f"Implementation planner generated implementation plan:\n{implementation_plan}")
            except Exception as e:
                self.logger.info(f"Exception encountered in implementation planner: {e}")
            implementation_planner.reset()

            try:
                implementation = implementer.solve_intermediate(problem_statement, problem_spec, implementation_signature, test_cases, implementation_plan)
                implementation = implementation_signature[:-len("sorry")] + implementation
                self.logger.info(f"Implementer generated implementation:\n{implementation}")
            except Exception as e:
                self.logger.info(f"Exception encountered in implementer: {e}")
            implementer.reset()

            implementation_passes = self._check_implementation(implementation, test_cases) # TODO: deal with commented test cases
            if implementation_passes: # TODO: provide feedback to implementer/implementation planner?
                self.logger.info("Implementer sample passed test cases.")
            else:
                self.logger.info("Implementer sample failed test cases.")
            
            if implementation_passes:
                self.logger.info(f"Implementer sample passed on attempt: {i+1} of {NUM_IMPLEMENTATION_SAMPLES}")
                break

        if implementation_passes:
            self.logger.info("Implementation passed test cases.")
        else:
            self.logger.info("Implementation failed test cases.")

        lemmas = []
        lemma_plans = []
        correctness_plan = "N/A"
        try:
            raw_proof_plan, lemmas, lemma_plans, correctness_plan = proof_planner.solve_intermediate(problem_statement, problem_spec, implementation, correctness_definition)
            assert len(lemmas) == len(lemma_plans)
            self.logger.info(f"Proof planner generated raw proof plan:\n{raw_proof_plan}")
        except Exception as e:
            self.logger.info(f"Exception encountered in proof planner: {e}")
        proof_planner.reset()

        # TODO: add provers

        proved = implementation_passes # TODO: make this actually reflect if problem is proved

        if proved:
            self.logger.info("Successfully proved correctness.")
        else:
            self.logger.info("Failed to prove correctness.")

        return proved

    def solve(self, problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str, correctness_definition: str, time_allowed: int) -> typing.Tuple[bool, str]:
        self.start_time = time.time()
        self.logger.info(f"Starting to solve problem:\n{problem_statement}")
        try:
            if self.strategy == CoordinationSolverStrategy.PLANNER_IMPLEMENTER_PLANNER_PROVER_CHAIN:
                proved = self._planner_implementer_planner_prover_chain(problem_statement, problem_spec, implementation_signature, test_cases, correctness_definition, time_allowed)
            else:
                raise NotImplementedError(f"Strategy {self.strategy} is not implemented.")
        except Exception as e:
            self.logger.info(f"Exception encountered in strategy, returning False : {e}")
            proved = False
        self.end_time = time.time()
        self.logger.info(f"Finished solving in {self.end_time - self.start_time} seconds.")
        self.reset()
        return proved
