import logging
import typing
import time
import math
import random
import copy
import tempfile
from sympy import *
from aimo_gaz.solver.abs_solver_and_tool import Solver, Tool
from aimo_gaz.solver.tools.old_planner_tool import OldPlannerTool
from aimo_gaz.solver.tools.old_code_tool import OldCodeTool
from aimo_gaz.solver.tools.execution_tool import ExecutionTool
from aimo_gaz.solver.tools.coordinator_tool import CoordinatorTool
from aimo_gaz.solver.tools.planner_tool import PlannerTool
from aimo_gaz.solver.tools.code_tool import CodeTool
from aimo_gaz.solver.tools.llm_guesser_tool import LLMGuesserTool
from aimo_gaz.solver.tools.prover_tool import ProverTool
from aimo_gaz.solver.tools.lean4_executor_tool import Lean4ExecutorTool
from aimo_gaz.solver.tools.coordinator_tool import ToolOrGlobalGuess
from aimo_gaz.scripts.eval import ProblemState, ProofEnvWrapper
from aimo_gaz.utils import string_utils, proof_utils
from enum import Enum
from collections import Counter

class CoordinationSolverStrategy(Enum):
    PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE = "plan_code_exec_extract_last_maj_vote"
    COORDINATOR_TOOL_HISTORY_LOOP = "coordinator_tool_history_loop"

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
        self.history_buffer = []
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
        self.history_buffer.clear()
    
    def _convert_float_to_rational(self, float_num: float) -> Rational:
        return Rational(float_num).limit_denominator()

    def _run_simplify(self, output, context):
        context["simp_output"] = simplify(output)

    # def _parse_integer(self, output):
    #     try:
    #         return float(output)
    #     except Exception as e:
    #         self.logger.info(f"Could not parse {output} as rational with exception {e}")
    #         try:
    #             if self._cloned_exec_tool is None:
    #                 self._cloned_exec_tool = copy.deepcopy(self.tools["executor"])
    #             self._cloned_exec_tool.reset()
    #             outs = self._cloned_exec_tool.solve_intermediate_parallel([f"print(simplify('{output}'))"])
    #             simpl_output, _ = self._cloned_exec_tool.extract_last_output(outs[0])
    #             self.logger.info(f"SymPy simplified output is {simpl_output}")
    #             return float(simpl_output)
    #         except Exception as e:
    #             self.logger.info(f"Could not parse {output} as sympy expression with exception {e}")
    #             return float(output)
    
    def _log_and_add_to_history_buffer(self, message):
        self.logger.info(message)
        self.history_buffer.append(message)


    def _coordinator_tool_history_loop(self, problem_statement: str, raw_theorem_statement: str, theorem_statement: str, problem_state: ProblemState, proof_env_wrapper: ProofEnvWrapper, name: str, time_allowed: int) -> float:
        assert len(self.tools) > 0, "No tools provided."
        assert "llm_guesser" in self.tools, "LLM guesser tool not provided."

        coordinator: CoordinatorTool = self.tools["coordinator"]
        planner: PlannerTool = self.tools["planner"]
        coder: CodeTool = self.tools["coder"]
        executor: ExecutionTool = self.tools["executor"]
        llm_guesser: LLMGuesserTool = self.tools["llm_guesser"]
        prover: ProverTool = self.tools["prover"]
        lean4_executor: Lean4ExecutorTool = self.tools["lean4_executor"]

        global_guess = None
        formatted_answer = None
        solution_str = None

        if problem_state == ProblemState.PROVING or problem_state == ProblemState.PROVING_AFTER_FINDING:
            proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env, solution_str)
            self._log_and_add_to_history_buffer(proof_state_render)

        time_left = time_allowed
        end_loop = False
        loop_num = 0
        while time_left > 0 and not end_loop:
            start_time = time.time()
            loop_num += 1

            coordinator_error = False
            try:
                tool_or_global_guess, tool_prompt, global_guess_temp = coordinator.solve_intermediate(self.history_buffer, problem_statement, theorem_statement, problem_state)
                self.history_buffer.clear()

                self._log_and_add_to_history_buffer(f"Loop {loop_num}: Coordinator chose tool: {None if tool_or_global_guess is None else tool_or_global_guess.value}")
            except Exception as e:
                self._log_and_add_to_history_buffer(f"Exception encountered in coordinator: {e}")
                coordinator_error = True

            if coordinator_error:
                pass
            elif tool_or_global_guess == ToolOrGlobalGuess.PLANNER:
                try:
                    plan = planner.solve_intermediate(problem_statement, theorem_statement, tool_prompt)

                    self._log_and_add_to_history_buffer(f"Planner generated plan:\n{plan}")
                except Exception as e:
                    self._log_and_add_to_history_buffer(f"Exception encountered in planner: {e}")

                planner.reset()
            elif tool_or_global_guess == ToolOrGlobalGuess.CODER:
                code = None
                try:
                    code = coder.solve_intermediate(problem_statement, theorem_statement, tool_prompt)
                except Exception as e:
                    self._log_and_add_to_history_buffer(f"Exception encountered in coder: {e}")
                
                if code is not None:
                    try:
                        output = executor.solve_intermediate(code) # TODO: maybe switch to multiple code generations and parallel execution

                        last_output, code_success = executor.extract_last_output(output)
                        if code_success:
                            self._log_and_add_to_history_buffer(f"Code executor output: {last_output}") # TODO: include entire code generated too?
                        else:
                            self._log_and_add_to_history_buffer(f"Code executor raised exception: {last_output}")
                    except Exception as e:
                        self._log_and_add_to_history_buffer(f"Exception encountered in code executor: {e}")
                
                coder.reset()
                executor.reset()
            elif tool_or_global_guess == ToolOrGlobalGuess.LLM_GUESSER:
                try:
                    guess = llm_guesser.solve_intermediate(problem_statement, theorem_statement, tool_prompt)

                    self._log_and_add_to_history_buffer(f"LLM guesser guessed:\n{guess}")
                except Exception as e:
                    self._log_and_add_to_history_buffer(f"Exception encountered in LLM guesser: {e}")

                llm_guesser.reset()
            elif tool_or_global_guess == ToolOrGlobalGuess.PROVER:
                if problem_state == ProblemState.PROVING or problem_state == ProblemState.PROVING_AFTER_FINDING:
                    try:
                        proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env, solution_str)
                        tactic = prover.solve_intermediate(problem_statement, theorem_statement, proof_state_render, tool_prompt)

                        self._log_and_add_to_history_buffer(f"Prover output tactic: {tactic}")
                    except Exception as e:
                        self._log_and_add_to_history_buffer(f"Exception encountered in prover: {e}")
                    
                    prover.reset()
                else:
                    self._log_and_add_to_history_buffer(f"Prover tool is invalid while the problem's answer is still being guessed.") # TODO: this won't be needed later
            elif tool_or_global_guess == ToolOrGlobalGuess.LEAN4_EXECUTOR:
                if problem_state == ProblemState.PROVING or problem_state == ProblemState.PROVING_AFTER_FINDING:
                    try:
                        tactic = tool_prompt
                        lean4_executor.solve_intermediate(proof_env_wrapper.proof_env, tactic)
                        
                        proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env, solution_str)
                        self._log_and_add_to_history_buffer(f"Lean 4 executor executed tactic: {tactic}\n\n{proof_state_render}")
                    except Exception as e:
                        self._log_and_add_to_history_buffer(f"Exception encountered in Lean 4 executor: {e}")
                    
                    lean4_executor.reset()
                    
                    if proof_env_wrapper.proof_env.done:
                        self.logger.info("Succesfully proved theorem, ending loop.")
                        end_loop = True
                else:
                    self._log_and_add_to_history_buffer(f"Lean 4 executor tool is invalid while the problem's answer is still being guessed.") # TODO: this won't be needed later
            elif tool_or_global_guess == ToolOrGlobalGuess.GLOBAL_GUESS:
                if problem_state == ProblemState.FINDING:
                    global_guess = global_guess_temp
                    self._log_and_add_to_history_buffer(f"Coordinator output global guess: {global_guess}")

                    # TODO: deal with noncomputable real division? (only an issue if guess is fraction of real numbers but actual solution is literal)
                    formatted_answer = coordinator.solve_intermediate_format_answer(self.history_buffer, theorem_statement)
                    self.history_buffer.clear()
                    self._log_and_add_to_history_buffer(f"Coordinator output formatted answer: {formatted_answer}")

                    new_raw_theorem_statement = raw_theorem_statement.replace("sorry", formatted_answer, 1)
                    self.logger.info(f"Lean theorem with answer inserted:\n{new_raw_theorem_statement}")

                    theorem_statement = string_utils.filter_theorem_statement(new_raw_theorem_statement)
                    self._log_and_add_to_history_buffer(f"Lean 4 Theorem Statement with Answer Inserted:\n{theorem_statement}")

                    temp_lean_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".lean")

                    temp_lean_file.write(new_raw_theorem_statement)
                    temp_lean_file.flush()

                    lean4_project_folder = proof_env_wrapper.proof_env.dynamic_proof_executor_callback.project_folder
                    temp_proof_env = proof_utils.get_proof_env(lean4_project_folder, temp_lean_file.name, name)
                    proof_env_wrapper.swap_proof_env(temp_proof_env, temp_lean_file)

                    problem_state = ProblemState.PROVING_AFTER_FINDING
                    solution_str = formatted_answer

                    proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env, solution_str)
                    self._log_and_add_to_history_buffer(proof_state_render)
                else:
                    self._log_and_add_to_history_buffer(f"Globally guessing is invalid while formally proving the theorem.")
            else:
                self._log_and_add_to_history_buffer(f"Coordinator-chosen tool '{tool_or_global_guess}' is invalid.")

            time_left -= math.ceil(time.time() - start_time)
            
            self.logger.info(f"End of loop {loop_num}. Time left: {time_left}\n")
        
        coordinator.reset()

        self.logger.info("Solver finished looping.")

        if problem_state == ProblemState.FINDING:
            self.logger.info("Failed to output global guess.")
        
        if proof_env_wrapper.proof_env.done:
            self.logger.info("Succesfully proved theorem.")
        else:
            self.logger.info("Failed to prove theorem.")
        
        return global_guess, formatted_answer


    def _plan_code_exec_extract_last_maj_vote(self, problem_statement: str, time_allowed: int) -> float:
        assert len(self.tools) > 0, "No tools provided."
        assert "old_planner" in self.tools, "OldPlanner tool not provided."
        assert "old_coder" in self.tools, "OldCoder tool not provided."
        assert "executor" in self.tools, "Executor tool not provided."
        old_planner: OldPlannerTool = self.tools["old_planner"]
        old_coder: OldCodeTool = self.tools["old_coder"]
        executor: ExecutionTool = self.tools["executor"]
        global_attempts, local_attempts = 0, 0
        # total_repairs = 0
        codes = []
        global_float_answers = []
        OLD_PLANNER_AVG_TIME, OLD_CODER_AVG_TIME, REPAIR_AVG_TIME = 0, 0, 0
        ATTEMPTS_TO_TRY = self.num_attempts
        TIME_LEFT = True
        CURR_TIME_LEFT = time_allowed
        # eps = 1e-6
        outer_attempts_to_try = 1
        while CURR_TIME_LEFT > 30 and TIME_LEFT and outer_attempts_to_try > 0:
            outer_attempts_to_try -= 1
            curr_time = time.time()
            # ATTEMPTS_TO_TRY = math.floor(CURR_TIME_LEFT/(OLD_PLANNER_AVG_TIME + OLD_CODER_AVG_TIME + 10)) if global_attempts != 0 else min(self.num_attempts, math.floor(CURR_TIME_LEFT/(OLD_PLANNER_AVG_TIME + OLD_CODER_AVG_TIME + 5)))
            ATTEMPTS_TO_TRY = 5
            self.logger.info(f"Giving {ATTEMPTS_TO_TRY} attempts on current problem. Time left {CURR_TIME_LEFT} with average call times old_planner: {OLD_PLANNER_AVG_TIME}, old_coder: {OLD_CODER_AVG_TIME}, repairer: {REPAIR_AVG_TIME}")
            if ATTEMPTS_TO_TRY <= 0:
                TIME_LEFT = False
                break
            while local_attempts < ATTEMPTS_TO_TRY and CURR_TIME_LEFT > 30:
                try:
                    # Plan
                    plan_start_time = time.time()
                    plan = old_planner.solve_intermediate(problem_statement)
                    OLD_PLANNER_AVG_TIME = (OLD_PLANNER_AVG_TIME + (time.time() - plan_start_time)) if global_attempts == 0 else (OLD_PLANNER_AVG_TIME * global_attempts + (time.time() - plan_start_time))/(global_attempts + 1)
                    # Code
                    old_coder.inference_kwargs["n"] = self.num_code_gens
                    old_coder_start_time = time.time()
                    codes_gen = old_coder.solve_intermediate(problem_statement=problem_statement, plan=plan)
                    OLD_CODER_AVG_TIME = (OLD_CODER_AVG_TIME + (time.time() - old_coder_start_time)) if global_attempts == 0 else (OLD_CODER_AVG_TIME * global_attempts + (time.time() - old_coder_start_time))/(global_attempts + 1)
                    if isinstance(codes_gen, str):
                        codes_gen = [codes_gen]
                    codes.extend(codes_gen)
                except Exception as e:
                    self.logger.info(f"Exception encountered in planning and coding phase: {e}")
                local_attempts += 1
                global_attempts += 1
                old_planner.reset()
                old_coder.reset()
                time_now = time.time()
                CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time_now - curr_time))
                curr_time = time_now
                self.logger.info(f"Time left after planning and coding is {CURR_TIME_LEFT}")
            
            # Execute
            executor.history = copy.deepcopy(old_coder.history)
            outputs = executor.solve_intermediate_parallel(codes)
            # Extract the last output
            last_outputs = [executor.extract_last_output(output)[0] for output in outputs]
            
            # See if this is a valid answer
            self.logger.info(f"Checking if executor outputs are valid answers.")
            float_answers = [None] * len(last_outputs)
            for i, output in enumerate(last_outputs):
                # try:
                #     float_answers[i] = self._parse_integer(output)
                #     if abs(int(float_answers[i]) - float_answers[i]) > eps:
                #         float_answers[i] = None
                # except Exception as e:
                #     self.logger.info(f"Could not parse {output}, with exception {e}")
                output = string_utils.parse_float(output)
                if output is None:
                    self.logger.info(f"Could not parse '{output}' as a float or fraction.")
                    continue
                float_answers[i] = output
            global_float_answers += float_answers

#             # collect the invalid answers, and have the model run the repair agent on those:
#             invalid_idxs = [i for i, answer in enumerate(float_answers) if answer is None]
#             fixed_codes = []
#             self.logger.info(f"Running the repair model on {len(invalid_idxs)} bad codes, indices are {invalid_idxs} and number of outputs is {len(last_outputs)}")
#             with self.tools['old_coder']:
#                 for idx in invalid_idxs:
#                     try:
#                         model = self.tools['old_coder'].model
#                         prompt = f"""User: Below is a math problem that has an integer solution and a python program which returns an output which is not the final solution.
# Solve the problem by writing a python program using sympy, you can use the result of the previous program.
# Make sure you code runs correctly! The answer to the problem should be an integer in range 0 to 999.
# Problem Description:
# {problem_statement}

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
#                         response = model.generate(prompt, **self.tools['old_coder'].inference_kwargs) # TODO: Does this augment the history?
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
#                         self.logger.info(f"Encountered exception during repair phase: {e}")
#                         pass
#                     time_now = time.time()
#                     CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time_now - curr_time))
#                     curr_time = time_now
#                     self.logger.info(f"Time left after repair is {CURR_TIME_LEFT}")
#                     if CURR_TIME_LEFT <= 30:
#                         break
#             if len(fixed_codes) > 0:
#                 repaired_outputs = executor.solve_intermediate_parallel(fixed_codes)
#                 # Extract the last output
#                 repaired_last_outputs = [executor.extract_last_output(output)[0] for output in repaired_outputs]
#             else:
#                 repaired_last_outputs = []
#             repaired_float_answers = [None] * len(repaired_last_outputs)
#             for i, output in enumerate(repaired_last_outputs):
#                 try:
#                     repaired_float_answers[i] = self._parse_integer(output)
#                     if abs(int(repaired_float_answers[i]) - repaired_float_answers[i]) > eps:
#                         repaired_float_answers[i] = None
#                 except Exception as e:
#                     self.logger.info(f"Could not parse {output} after repair, with exception {e}")
#                     pass
#             global_float_answers += repaired_float_answers
            local_attempts = 0
            CURR_TIME_LEFT = math.floor(CURR_TIME_LEFT - (time.time() - curr_time))

        # Take the majority non-None
        answers = [answer for answer in global_float_answers if answer is not None]
        self.logger.info(f"Taking the majority vote: global_float_answers: {global_float_answers}, answers: {answers}")
        self.logger.info(f"Model's generated answers are {answers}")
        if len(answers) == 0:
            self.logger.info("No answers found, returning 0.0")
            return 0.0
        else:
            self.logger.info("Answers found.")
            answer_counter = Counter(answers) # TODO: Counter may not work well with float keys
            most_common_answers = answer_counter.most_common(2)
            if len(most_common_answers) == 1:
                most_common_answer = most_common_answers[0][0]
            elif len(most_common_answers) == 2 and most_common_answers[0][1] > most_common_answers[1][1]:
                # There is no tie in the majority vote
                most_common_answer = most_common_answers[0][0]
            else:
                most_common_answer = None
            if (most_common_answer is not None and self.picker_optional) or len(answer_counter) == 1:
                answer = most_common_answer
                self.logger.info(f"Will not run pick answer, as the majority vote is {answer}")
                return answer
            try:
                with self.tools['old_coder']:
                    model = self.tools['old_coder'].model
                    choices = '\n'.join([f'( {chr(65 + i)} ) {answer}' for i, answer in enumerate(set(answers))]) # TODO: set() may not work well with floats
                    prompt = f"""Below is a problem description. Which answer do you think is best?

Problem Description:
{problem_statement}

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
                    response = model.generate(prompt, **self.tools['old_coder'].inference_kwargs)
                    outs = model.parse_out(response)
                    self.logger.info(f"Picked answer:\n {outs[0][0]}")
                    most_common_answer = outs[0][0].split("\\boxed{")
                    if len(most_common_answer) > 1 and len(most_common_answer[-1]) > 0:
                        most_common_answer = most_common_answer[-1]
                    else:
                        raise Exception("Couldn't parse the answer.")

                    # get which letter is in most_common_answer
                    answer_chosen = False
                    for i, answer in enumerate(answers):
                        if chr(65 + i) in most_common_answer or str(answer) == most_common_answer: # TODO: This probably doesn't work well for floats
                            most_common_answer = answer
                            answer_chosen = True
                            break
                    if not answer_chosen:
                        raise Exception("Couldn't parse the answer.")

                    answer = most_common_answer
            except Exception as e:
                answer_counter = Counter(answers)
                most_common_answer = answer_counter.most_common(1)[0][0]
                most_common_answer_count = answer_counter.most_common(1)[0][1]
                if most_common_answer_count > 1:
                    answer = most_common_answer
                else:
                    answer = random.choice(answers)
            return answer

    def solve(self, problem_statement: str, raw_theorem_statement: str, theorem_statement: str, problem_state: ProblemState, proof_env_wrapper: ProofEnvWrapper, name: str, time_allowed: int) -> typing.Tuple[bool, str]:
        assert len(self.tools) > 0, "No tools provided."
        self.start_time = time.time()
        self.logger.info(f"Starting to solve problem:\n{problem_statement}")
        answer = -1
        try:
            if self.strategy == CoordinationSolverStrategy.PLAN_CODE_EXEC_EXRACT_LAST_MAJ_VOTE:
                answer = self._plan_code_exec_extract_last_maj_vote(problem_statement, time_allowed)
            elif self.strategy == CoordinationSolverStrategy.COORDINATOR_TOOL_HISTORY_LOOP:
                answer = self._coordinator_tool_history_loop(problem_statement, raw_theorem_statement, theorem_statement, problem_state, proof_env_wrapper, name, time_allowed)
            else:
                raise NotImplementedError(f"Strategy {self.strategy} is not implemented.")
        except Exception as e:
            self.logger.info(f"Exception encountered in strategy, returning 0.0 : {e}")
            answer = 0.0
        self.end_time = time.time()
        self.logger.info(f"Finished solving in {self.end_time - self.start_time} seconds.")
        self.reset()
        return answer
