import logging
import typing
import time
import math
import random
import copy
from sympy import *
from aimo_gaz.solver.abs_solver_and_tool import Solver, Tool
from aimo_gaz.solver.tools.planner_tool import PlannerTool
from aimo_gaz.solver.tools.code_tool import CodeTool
from aimo_gaz.solver.tools.execution_tool import ExecutionTool
from enum import Enum
from collections import Counter

class CoordinationSolverStrategy(Enum):
    PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE = "plan_code_exec_extract_last_maj_vote"

    def __str__(self):
        return self.value

class CoordinationSolver(Solver):
    def __init__(self,
        tools: typing.Dict[str, Tool],
        strategy: CoordinationSolverStrategy,
        logger: logging.Logger = None,
        **coordination_kwargs):
        self.logger = logger
        self.tools = tools
        self.strategy = strategy
        self.coordination_kwargs = coordination_kwargs
        self.history = []
        self._init_hyperparameters()
        self._cloned_exec_tool : ExecutionTool = None
    
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
        pass

    def reset(self):
        for tool in self.tools.values():
            tool.reset()
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
                if self._cloned_exec_tool is None:
                    self._cloned_exec_tool = copy.deepcopy(self.tools["executor"])
                self._cloned_exec_tool.reset()
                outs = self._cloned_exec_tool.solve_intermediate_parallel([f"print(simplify('{output}'))"])
                simpl_output = self._cloned_exec_tool.extract_last_output(outs[0])
                self.logger.info(f"Sympy simplified output is {simpl_output}")
                return float(simpl_output)
            except Exception as e:
                self.logger.info(f"Could not parse {output} as sympy expression with exception {e}.")
                return float(output)


    def plan_code_exec_extract_last_maj_vote(self, problem_description: str, time_allowed: int) -> int:
        assert len(self.tools) > 0, "No tools provided."
        assert "planner" in self.tools, "Planner tool not provided."
        assert "coder" in self.tools, "Coder tool not provided."
        assert "executor" in self.tools, "Executor tool not provided."
        planner: PlannerTool = self.tools["planner"]
        coder: CodeTool = self.tools["coder"]
        executor: ExecutionTool = self.tools["executor"]
        global_attempts, local_attempts = 0, 0
        # total_repairs = 0
        codes = []
        global_float_answers = []
        PROBLEM_STARTING_TIME, PLANNER_AVG_TIME, CODER_AVG_TIME, REPAIR_AVG_TIME = time.time(), 0, 0, 0
        ATTEMPTS_TO_TRY = self.num_attempts
        TIME_LEFT = True
        CURR_TIME_LEFT = time_allowed
        eps = 10e-6
        outer_attempts_to_try = 1
        while CURR_TIME_LEFT > 30 and TIME_LEFT and outer_attempts_to_try > 0:
            outer_attempts_to_try -= 1
            curr_time = time.time()
            # ATTEMPTS_TO_TRY = math.floor(CURR_TIME_LEFT/(PLANNER_AVG_TIME + CODER_AVG_TIME + 10)) if global_attempts != 0 else min(self.num_attempts, math.floor(CURR_TIME_LEFT/(PLANNER_AVG_TIME + CODER_AVG_TIME + 5)))
            ATTEMPTS_TO_TRY = 5
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
                    coder.inference_kwargs["n"] = self.num_code_gens
                    coder_start_time = time.time()
                    codes_gen = coder.solve_intermediate(problem_description=problem_description, plan=plan)
                    CODER_AVG_TIME = (CODER_AVG_TIME + (time.time() - coder_start_time)) if global_attempts == 0 else (CODER_AVG_TIME * global_attempts + (time.time() - coder_start_time))/(global_attempts + 1)
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
                    if abs(int(float_answers[i]) - float_answers[i]) > eps:
                        float_answers[i] = None
                except Exception as e:
                    self.logger.info(f"Could not parse {output}, with exception {e}.")
                    pass
            global_float_answers += float_answers

#             # collect the invalid answers, and have the model run the repair agent on those:
#             invalid_idxs = [i for i, answer in enumerate(float_answers) if answer is None]
#             fixed_codes = []
#             self.logger.info(f"Running the repair model on {len(invalid_idxs)} bad codes, indices are {invalid_idxs} and number of outputs is {len(last_outputs)}")
#             with self.tools['coder']: 
#                 for idx in invalid_idxs: 
#                     try:
#                         model = self.tools['coder'].model
#                         prompt = f"""User: Below is a math problem that has an integer solution and a python program which returns an output which is not the final solution. 
# Solve the problem by writing a python program using sympy, you can use the result of the previous program. 
# Make sure you code runs correctly! The answer to the problem should be an integer in range 0 to 999.
# Problem Description: 
# {problem_description}

# ```python
# {codes[idx]}
# ```
# ```output
# {last_outputs[idx]}
# ```

# Write python code using sympy which solves the problem. 
# Think step by step, make sure the code runs correctly and that the final solution is an integer! 
# Do not copy the above code, instead fix it up so that it finishes by printing the final answer. 
# Your code should finish by printing the final answer. The answer to the problem should be an integer in range 0 to 999.
# Assistant:
# ```python code:
# """
#                         repair_start_time = time.time()
#                         self.logger.info(f"[REPAIR] Prompting the model with:\n{prompt}")
#                         response = model.generate(prompt, **self.tools['coder'].inference_kwargs) # TODO: Does this augment the history?
#                         REPAIR_AVG_TIME =  (REPAIR_AVG_TIME + time.time() - repair_start_time) if total_repairs == 0 else (total_repairs * REPAIR_AVG_TIME + time.time() - repair_start_time) / (1 + total_repairs)
#                         total_repairs += 1
#                         # uses the same stop tokens so we should be good on that end
#                         outs = model.parse_out(response)
#                         assert len(outs) == 1
#                         for result in outs:
#                             for gen_text in result:
#                                 self.logger.info(f"Repair phase: Output generated code, before cleaning, is {gen_text}")
#                                 # if gen_text.endswith('[END CODE]'):
#                                 #     fixed_codes.append("    " + gen_text.replace('[END CODE]', ''))
#                                 # elif gen_text.endswith('```'):
#                                 #     fixed_codes.append("    " + gen_text.replace('```', ''))
#                                 # elif gen_text.endswith('<｜end▁of▁sentence｜>'):
#                                 #     fixed_codes.append("    " + gen_text.replace('<｜end▁of▁sentence｜>', ''))
#                                 # else:
#                                 #     fixed_codes.append(f"    {gen_text}")
#                                 fixed_codes.append(f"    {gen_text}")
#                     except Exception as e:
#                         self.logger.info(f"Encountered exception during repair phase: {e}.")
#                         pass
                    # time_now = time.time()
                    # CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time_now - curr_time))
                    # curr_time = time_now
                    # self.logger.info(f"Time left after repair is {CURR_TIME_LEFT}")
                    # if CURR_TIME_LEFT <= 30:
                    #     break
            # if len(fixed_codes) > 0:
            #     repaired_outputs = executor.solve_intermediate_parallel(fixed_codes)
            #     # Extract the last output
            #     repaired_last_outputs = [executor.extract_last_output(output) for output in repaired_outputs]
            # else:
            #     repaired_last_outputs = []
            # repaired_float_answers = [None] * len(repaired_last_outputs)
            # for i, output in enumerate(repaired_last_outputs):
            #     try:
            #         repaired_float_answers[i] = self._parse_integer(output)
            #         if abs(int(repaired_float_answers[i]) - repaired_float_answers[i])  > eps:
            #             repaired_float_answers[i] = None
            #     except Exception as e:
            #         self.logger.info(f"Could not parse {output} after repair, with exception {e}.")
            #         pass
            # global_float_answers += repaired_float_answers
            local_attempts = 0
            CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time.time() - curr_time))

        # Take the majority non-None
        answers = [answer for answer in global_float_answers if answer is not None and (answer > 0)]
        bad_answers = [abs(answer) for answer in global_float_answers if answer is not None and (answer <= 0)]
        self.logger.info(f"Taking the majority vote: global_float_answers: {global_float_answers} answers: {answers}, bad_answers: {bad_answers}")
        if len(answers) == 0:
            if len(bad_answers) == 0:
                self.logger.info("No answers found, choosing random number.")
                return random.randint(0,999)
            else:
                self.logger.info("Only bad answers found.")
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
            self.logger.info("Answers found.")
            answer_counter = Counter(answers)
            most_common_answers = answer_counter.most_common(2)
            if len(most_common_answers) == 1:
                most_common_answer = most_common_answers[0][0]
            elif len(most_common_answers) == 2 and most_common_answers[0][1] > most_common_answers[1][1]:
                # There is no tie in the majority vote
                most_common_answer = most_common_answers[0][0]
            else:
                most_common_answer = None
            if (most_common_answer is not None and self.picker_optional) or len(answer_counter) == 1:
                int_answer = int(most_common_answer)
                mod_answer = int_answer % 1000
                self.logger.info(f"Will not run pick answer, as the majority vote is {mod_answer}")
                self.logger.info(f"Model's generated answers are {answers}")
                return mod_answer
            try:
                with self.tools['coder']:
                    model = self.tools['coder'].model
                    choices = '\n'.join([f'( {chr(65 + i)} ) {answer}' for i, answer in enumerate(answers)])
                    prompt = f"""Below is a problem description. Which answer do you think is best?

Problem Description: 
{problem_description}

Choices:
{choices}
                    """.strip() + "\n\nPlease reason step by step, and put your final answer within \\boxed{}."
                    prompt = [
                        {
                            "role": "user",
                            "content": prompt
                        },
                    ]
                    self.logger.info(f"[PICK ANSWER] Prompting the model with:\n{prompt}")
                    response = model.generate(prompt, **self.tools['coder'].inference_kwargs)
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
                        if chr(65 + i) in most_common_answer or str(answer) == most_common_answer:
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
        assert len(self.tools) > 0, "No tools provided."
        self.start_time = time.time()
        self.logger.info(f"Starting to solve problem: {problem_description}")
        answer = -1
        try:
            if self.strategy == CoordinationSolverStrategy.PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE:
                answer = self.plan_code_exec_extract_last_maj_vote(problem_description, time_allowed)
            else:
                raise NotImplementedError(f"Strategy {self.strategy} is not implemented.")
        except Exception as e:
            self.logger.info(f"Exception encountered in strategy, choosing random answer : {e}")
            answer = random.randint(0,999)
        self.end_time = time.time()
        self.logger.info(f"Finished solving in {self.end_time - self.start_time} seconds.")
        self.reset()
        return answer
