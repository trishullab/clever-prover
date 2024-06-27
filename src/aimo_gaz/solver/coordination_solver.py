import logging
import typing
import time
import math
import random
import copy
import multiprocessing
from sympy import *
from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.solver.planner_solver import PlannerSolver
from aimo_gaz.solver.code_solver import CodeSolver
from aimo_gaz.solver.execution_solver import ExecutionSolver
# from aimo_gaz.solver.ask_vote import AskVote
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
        self.num_attempts = self.coordination_kwargs.get("num_attempts", 5)
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
    
    def _convert_float_to_rational(self, float_num: float) -> Rational:
        return Rational(float_num).limit_denominator()

    def _run_simplify(self, output, context):
        context["simp_output"] = simplify(output)

    def _parse_integer(self, output):
        try:
            return float(output)
        except Exception as e:
            self.logger.info(f"Could not parse {output} as rational with exception {e}.")
            try:
                context = multiprocessing.Manager().dict()
                simplfiy_job = multiprocessing.Process(target=self._run_simplify, args=(output, context))
                try:
                    simplfiy_job.start()
                    simplfiy_job.join(timeout=5)
                except Exception as e:
                    simplfiy_job.terminate()
                    simplfiy_job.join()
                simpl_output = context.get("simp_output", None)
                self.logger.info(f"Sympy output is {simpl_output}")
                return float(simpl_output)
            except Exception as e:
                self.logger.info(f"Could not parse {output} as sympy expression with exception {e}.")
                return float(output)


    def plan_code_exec_extract_last_maj_vote(self, problem_description: str, time_allowed: int) -> int:
        assert len(self.solvers) > 0, "No solvers provided."
        assert "planner" in self.solvers, "Planner solver not provided."
        assert "coder" in self.solvers, "Coder solver not provided."
        assert "executor" in self.solvers, "Executor solver not provided."
        planner: PlannerSolver = self.solvers["planner"]
        coder: CodeSolver = self.solvers["coder"]
        executor: ExecutionSolver = self.solvers["executor"]
        global_attempts, local_attempts = 0, 0
        total_repairs = 0
        codes = []
        global_float_answers = []
        PROBLEM_STARTING_TIME, PLANNER_AVG_TIME, CODER_AVG_TIME, REPAIR_AVG_TIME = time.time(), 0, 0, 0
        ATTEMPTS_TO_TRY = self.num_attempts
        TIME_LEFT = True
        CURR_TIME_LEFT = time_allowed 
        eps = 10e-6
        while CURR_TIME_LEFT > 30 and TIME_LEFT:
            curr_time = time.time()
            ATTEMPTS_TO_TRY = math.floor(CURR_TIME_LEFT/(PLANNER_AVG_TIME + CODER_AVG_TIME + 10)) if global_attempts != 0 else min(self.num_attempts, math.floor(CURR_TIME_LEFT/(PLANNER_AVG_TIME + CODER_AVG_TIME + 5)))
            self.logger.info(f"Giving {ATTEMPTS_TO_TRY} attempts on current problem. Time left {CURR_TIME_LEFT} with average call times planner: {PLANNER_AVG_TIME}, coder: {CODER_AVG_TIME}, repairer: {REPAIR_AVG_TIME}")
            if ATTEMPTS_TO_TRY <= 0:
                TIME_LEFT = False
                break
            while local_attempts < ATTEMPTS_TO_TRY and CURR_TIME_LEFT > 30:
                try:
                    # Plan
                    plan_start_time = time.time()
                    plan = planner.solve_intermediate(problem_description)
                    PLANNER_AVG_TIME = (PLANNER_AVG_TIME + (time.time() - plan_start_time)) if global_attempts == 0 else (PLANNER_AVG_TIME * global_attempts + (time.time() - plan_start_time))/(global_attempts + 1)
                    # Code
                    coder.inference_kwargs["num_return_sequences"] = self.num_code_gens
                    coder_start_time = time.time()
                    codes_gen = coder.solve_intermediate(problem_description=problem_description, plan=plan)
                    CODER_AVG_TIME = CODER_AVG_TIME + (time.time() - coder_start_time) if global_attempts == 0 else (CODER_AVG_TIME * global_attempts + (time.time() - coder_start_time))/(global_attempts + 1)
                    if isinstance(codes_gen, str):
                        codes_gen = [codes_gen]
                    codes.extend(codes_gen)
                except Exception as e:
                    self.logger.info(f"Exception encountered in planning and coding phase: {e}.")
                    pass
                local_attempts += 1
                global_attempts += 1
                planner.reset()
                coder.reset()
                time_now = time.time()
                CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time_now - curr_time))
                curr_time = time_now
                self.logger.info(f"Time left after planning and coding is {CURR_TIME_LEFT}")
            # Execute
            executor.history = copy.deepcopy(coder.history)
            outputs = executor.solve_intermediate_parallel(codes)
            # Extract the last output
            last_outputs = [executor.extract_last_output(output) for output in outputs]
            # See if this is a valid answer
            float_answers = [None] * len(last_outputs)
            for i, output in enumerate(last_outputs):
                try:
                    float_answers[i] = self._parse_integer(output)
                    # rational_pattern = r'Rational\((\d+),(\d+)\)'
                    # match = re.search(rational_pattern, output)
                    # if match:
                    #     float_answers[i] = float(match.group(1)) + float(match.group(2))
                    # else:
                    #     float_answers[i] = float(output)
                    
                    if abs(int(float_answers[i]) - float_answers[i])  > eps:
                        float_answers[i] = None
                except Exception as e:
                    self.logger.info(f"Could not parse {output}, with exception {e}.")
                    pass
            # TODO: collect the invalid answers, and have the model run the repair agent on those:
            global_float_answers += float_answers
            invalid_idxs = [i for i, answer in enumerate(float_answers) if answer is None]
            fixed_codes = []
            self.logger.info(f"Running the repair model on {len(invalid_idxs)} bad codes, indices are {invalid_idxs} and number of outputs is {len(last_outputs)}")
            with self.solvers['coder']: 
                for idx in invalid_idxs: 
                    try:
                        model = self.solvers['coder'].model
                        prompt = f"""User: Below is a math problem that has an integer solution and a python program which returns an output which is not the final solution. 
Solve the problem by writing a python program using sympy, you can use the result of the previous program. 
Make sure you code runs correctly! The answer to the problem should be an integer in range 0 to 999.
Problem Description: 
{problem_description}

```python
{codes[idx]}
```
```output
{last_outputs[idx]}
```

Write python code using sympy which solves the problem. 
Think step by step, make sure the code runs correctly and that the final solution is an integer! 
Do not copy the above code, instead fix it up so that it finishes by printing the final answer. 
Your code should finish by printing the final answer. The answer to the problem should be an integer in range 0 to 999.
Assistant:
```python code:
"""
                        repair_start_time = time.time()
                        self.logger.info(f"[REPAIR] Prompting the model with:\n{prompt}")
                        response = model.generate(prompt, **self.solvers['coder'].inference_kwargs) # TODO: Does this augment the history?
                        REPAIR_AVG_TIME =  (REPAIR_AVG_TIME + time.time() - repair_start_time) if total_repairs == 0 else (total_repairs * REPAIR_AVG_TIME + time.time() - repair_start_time) / (1 + total_repairs)
                        total_repairs += 1
                        # uses the same stop tokens so we should be good on that end
                        outs = model.parse_out(response)
                        assert len(outs) == 1
                        for result in outs:
                            for gen_text in result:
                                self.logger.info(f"Repair phase: Output generated code, before cleaning, is {gen_text}")
                                if gen_text.endswith('[END CODE]'):
                                    fixed_codes.append("    " + gen_text.replace('[END CODE]', ''))
                                elif gen_text.endswith('```'):
                                    fixed_codes.append("    " + gen_text.replace('```', ''))
                                elif gen_text.endswith('<｜end▁of▁sentence｜>'):
                                    fixed_codes.append("    " + gen_text.replace('<｜end▁of▁sentence｜>', ''))
                                else:
                                    fixed_codes.append(f"    {gen_text}")
                    except Exception as e:
                        self.logger.info(f"Encountered exception during repair phase: {e}.")
                        pass
                    time_now = time.time()
                    CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time_now - curr_time))
                    curr_time = time_now
                    self.logger.info(f"Time left after repair is {CURR_TIME_LEFT}")
                    if CURR_TIME_LEFT <= 30:
                        break
            if len(fixed_codes) > 0:
                repaired_outputs = executor.solve_intermediate_parallel(fixed_codes)
                # Extract the last output
                repaired_last_outputs = [executor.extract_last_output(output) for output in repaired_outputs]
            else:
                repaired_last_outputs = []
            repaired_float_answers = [None] * len(repaired_last_outputs)
            for i, output in enumerate(repaired_last_outputs):
                try:
                    repaired_float_answers[i] = self._parse_integer(output)
                    # rational_pattern = r'Rational\((\d+),(\d+)\)'
                    # match = re.search(rational_pattern, output)
                    # if match:
                    #     repaired_float_answers[i] = float(match.group(1)) + float(match.group(2))
                    # else:
                    #     repaired_float_answers[i] = float(output)
                    
                    if abs(int(repaired_float_answers[i]) - repaired_float_answers[i])  > eps:
                        repaired_float_answers[i] = None
                except Exception as e:
                    self.logger.info(f"Could not parse {output} after repair, with exception {e}.")
                    pass
            global_float_answers += repaired_float_answers
            local_attempts = 0
            CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time.time() - curr_time))
        # Take the majority non-None
        answers = [answer for answer in global_float_answers if answer is not None and (answer > 0)]
        bad_answers = [abs(answer) for answer in global_float_answers if answer is not None and (answer <= 0)]
        if len(answers) == 0:
            if len(bad_answers) == 0:
                return random.randint(0,999)
            else:
                answer_counter = Counter(bad_answers)
                most_common_answer = answer_counter.most_common(1)[0][0]
                most_common_answer_count = answer_counter.most_common(1)[0][1]
                if most_common_answer_count > 1:
                    int_answer = int(most_common_answer)
                    mod_answer = int_answer % 1000
                else:
                    mod_answer = int(random.choice(bad_answers))
                    mod_answer = mod_answer % 1000
                return mod_answer
        else:
            try:
                with self.solvers['coder']:
                    model = self.solvers['coder'].model
                    choices = '\n'.join([f'( {chr(65 + i)} ) {answer}' for i, answer in enumerate(answers)])
                    prompt = f"""User: Below is a problem description. Which answer do you think is best?

Problem Description: 
{problem_description}

Choices:
{choices}
                    """.strip() + """\n\nPlease reason step by step, and put your final answer within \\boxed{}.
Assistant:
                    """.rstrip()
                    prompt += '\n'
                    self.logger.info(f"[PICK ANSWER] Prompting the model with:\n{prompt}")
                    response = model.generate(prompt, **self.solvers['coder'].inference_kwargs)
                    outs = model.parse_out(response)
                    self.logger.info(f"Picked answer:\n {outs[0][0]}")
                    # most_common_answer = outs[0][0][0:min(10, len(outs[0][0]))]
                    most_common_answer = outs[0][0].split("\\boxed{")
                    if len(most_common_answer) > 1 and len(most_common_answer[-1]) > 0:
                        most_common_answer = most_common_answer[-1][0]
                    else:
                        raise Exception("Couldn't parse the answer.")

                    # get which letter is in most_common_answer
                    for i, answer in enumerate(answers):
                        if chr(65 + i) in most_common_answer:
                            most_common_answer = answer
                            break

                    int_answer = int(most_common_answer)
                    mod_answer = int_answer % 1000
            except Exception as e:
                answer_counter = Counter(answers)
                most_common_answer = answer_counter.most_common(1)[0][0]
                most_common_answer_count = answer_counter.most_common(1)[0][1]
                if most_common_answer_count > 1:
                    int_answer = int(most_common_answer)
                    mod_answer = int_answer % 1000
                else:
                    mod_answer = int(random.choice(answers))
                    mod_answer = mod_answer % 1000
            self.logger.info(f"Model's generated answers are {answers}")
            return mod_answer

    def solve(self, problem_description: str, time_allowed: int) -> int:
        assert len(self.solvers) > 0, "No solvers provided."
        self.start_time = time.time()
        self.logger.info(f"Starting to solve problem: {problem_description}")
        answer = -1
        try:
            if self.stragegy == CoordinationSolverStrategy.PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE:
                answer = self.plan_code_exec_extract_last_maj_vote(problem_description, time_allowed)
            else:
                raise NotImplementedError(f"Strategy {self.stragegy} is not implemented.")
        except Exception as e:
            self.logger.info(f"Exception encountered in strategy : {e}")
            answer = random.randint(0,999)
        self.end_time = time.time()
        self.logger.info(f"Finished solving in {self.end_time - self.start_time} seconds.")
        self.reset()
        return answer
