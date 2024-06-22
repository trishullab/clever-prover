import logging
import typing
import time
from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.solver.planner_solver import PlannerSolver
from aimo_gaz.solver.code_solver import CodeSolver
from aimo_gaz.solver.execution_solver import ExecutionSolver
from enum import Enum
from collections import Counter

class CoordinationSolverStrategy(Enum):
    PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE = "plan_code_exec_extract_last_maj_vote"

    def __str__(self):
        return self.value

class CoordinationSolver(Solver):
    def __init__(self, 
        solvers: typing.Dict[str, Solver], 
        startegy: CoordinationSolverStrategy, 
        logger: logging.Logger = None, 
        **coordination_kwargs):
        self.logger = logger
        self.solvers = solvers
        self.stragegy = startegy
        self.coordination_kwargs = coordination_kwargs
        self.history = []
        self._init_hyperparameters()
    
    def _init_hyperparameters(self):
        self.num_code_gens = self.coordination_kwargs.get("num_code_gens", 1)
        self.num_plans = self.coordination_kwargs.get("num_plans", 1)
        self.code_timeout_in_secs = self.coordination_kwargs.get("code_timeout_in_secs", 2*60) # 2 minutes default
        self.problem_timeout_in_secs = self.coordination_kwargs.get("problem_timeout_in_secs", 20*60) # 20 minutes default
        self.start_time = None
        self.end_time = None

    def solve_intermediate(self, problem_description: str) -> str:
        raise NotImplementedError("This solver does not solve problems partially.")

    def __enter__(self):
        for solver in self.solvers.values():
            solver.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for solver in self.solvers.values():
            solver.__exit__(exc_type, exc_val, exc_tb)
        pass

    def reset(self):
        for solver in self.solvers.values():
            solver.reset()
        self.history = []

    def plan_code_exec_extract_last_maj_vote(self, problem_description: str) -> int:
        assert len(self.solvers) > 0, "No solvers provided."
        assert "planner" in self.solvers, "Planner solver not provided."
        assert "coder" in self.solvers, "Coder solver not provided."
        assert "executor" in self.solvers, "Executor solver not provided."
        planner: PlannerSolver = self.solvers["planner"]
        coder: CodeSolver = self.solvers["coder"]
        executor: ExecutionSolver = self.solvers["executor"]
        # Plan
        plan = planner.solve_intermediate(problem_description)
        # Code
        coder.history = planner.history.copy() # Coder should know the plan with full context
        coder.inference_kwargs["num_return_sequences"] = self.num_code_gens
        codes = coder.solve_intermediate(plan)
        if isinstance(codes, str):
            codes = [codes]
        # Execute
        executor.history = coder.history.copy()
        outputs = executor.solve_intermediate_parallel(codes)
        # Extract the last output
        last_outputs = [executor.extract_last_output(output) for output in outputs]
        # See if this is a valid answer
        float_answers = [None] * len(last_outputs)
        for i, output in enumerate(last_outputs):
            try:
                float_answers[i] = float(output)
            except:
                pass
        # Take the majority non-None non-negative answer
        answers = [answer for answer in float_answers if answer is not None and answer >= 0]
        if len(answers) == 0:
            return -1
        else:
            answer_counter = Counter(answers)
            most_common_answer = answer_counter.most_common(1)[0][0]
            int_answer = int(most_common_answer)
            mod_answer = int_answer % 1000
            return mod_answer

    def solve(self, problem_description: str) -> int:
        assert len(self.solvers) > 0, "No solvers provided."
        self.start_time = time.time()
        self.logger.info(f"Starting to solve problem: {problem_description}")
        answer = -1
        if self.stragegy == CoordinationSolverStrategy.PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE:
            answer = self.plan_code_exec_extract_last_maj_vote(problem_description)
        else:
            raise NotImplementedError(f"Strategy {self.stragegy} is not implemented.")
        self.end_time = time.time()
        self.logger.info(f"Finished solving in {self.end_time - self.start_time} seconds.")
        self.reset()
        return answer
