import logging
import typing
import time
import math
import random
import copy
import tempfile
import subprocess
from sympy import *
from itp_interface.rl.simple_proof_env import ProofAction
from aimo_gaz.solver.abs_solver_and_tool import Solver, Tool
from aimo_gaz.solver.tools.implementation_planner_tool import ImplementationPlannerTool
from aimo_gaz.solver.tools.implementer_tool import ImplementerTool
from aimo_gaz.solver.tools.proof_planner_tool import ProofPlannerTool
from aimo_gaz.scripts.eval import ProblemState, ProofEnvWrapper
from aimo_gaz.utils import string_utils, proof_utils
from enum import Enum
from collections import Counter

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

        implementation_plan = "N/A"
        try:
            implementation_plan = implementation_planner.solve_intermediate(problem_statement, problem_spec, implementation_signature, test_cases)
            self.logger.info(f"Implementation planner generated implementation plan:\n{implementation_plan}")
        except Exception as e:
            self.logger.info(f"Exception encountered in implementation planner: {e}")
        implementation_planner.reset()

        implementation = implementation_signature
        try:
            implementation = implementer.solve_intermediate(problem_statement, problem_spec, implementation_signature, test_cases, implementation_plan)
            implementation = implementation_signature[:-len("sorry")] + implementation
            self.logger.info(f"Implementer generated implementation:\n{implementation}")
        except Exception as e:
            self.logger.info(f"Exception encountered in implementer: {e}")
        implementer.reset()

        implementation_passes = self._check_implementation(implementation, test_cases)
        if implementation_passes: # TODO: re-sample implementation if it fails test cases
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

        proved = True

        if proved:
            self.logger.info("Successfully proved correctness.")
        else:
            self.logger.info("Failed to prove correctness.")

        return proved


    # def _coordinator_tool_history_loop(self, problem_statement: str, raw_theorem_statement: str, theorem_statement: str, problem_state: ProblemState, proof_env_wrapper: ProofEnvWrapper, name: str, time_allowed: int) -> float:
    #     assert len(self.tools) > 0, "No tools provided."
    #     assert "llm_guesser" in self.tools, "LLM guesser tool not provided."

    #     coordinator: CoordinatorTool = self.tools["coordinator"]
    #     planner: PlannerTool = self.tools["planner"]
    #     coder: CoderTool = self.tools["coder"]
    #     executor: ExecutorTool = self.tools["executor"]
    #     llm_guesser: LLMGuesserTool = self.tools["llm_guesser"]
    #     prover: ProverTool = self.tools["prover"]

    #     answer = None
    #     formatted_answer = None

    #     if problem_state == ProblemState.PROVING or problem_state == ProblemState.PROVING_AFTER_FINDING:
    #         proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env)
    #         self._log_and_add_to_history_buffer(proof_state_render)

    #     time_left = time_allowed
    #     end_loop = False
    #     loop_num = 0
    #     while time_left > 0 and not end_loop:
    #         start_time = time.time()
    #         loop_num += 1

    #         coordinator_error = False
    #         try:
    #             tool_or_other, tool_prompt, answer_temp = coordinator.solve_intermediate(self.history_buffer, problem_statement, theorem_statement, problem_state)
    #             self.history_buffer.clear()

    #             self._log_and_add_to_history_buffer(f"Loop {loop_num}: Coordinator chose: {None if tool_or_other is None else tool_or_other.value}")
    #         except Exception as e:
    #             self._log_and_add_to_history_buffer(f"Exception encountered in coordinator: {e}")
    #             coordinator_error = True

    #         if coordinator_error:
    #             pass
    #         elif tool_or_other is None:
    #             self._log_and_add_to_history_buffer("Exception: Coordinator output must include the keyword '[TOOL]' (with a valid tool name)") # TODO: maybe move this error inside coordinator prompter
    #         elif tool_or_other == ToolOrOther.PLANNER:
    #             try:
    #                 plan = planner.solve_intermediate(tool_prompt)

    #                 self._log_and_add_to_history_buffer(f"Planner generated plan:\n{plan}")
    #             except Exception as e:
    #                 self._log_and_add_to_history_buffer(f"Exception encountered in planner: {e}")

    #             planner.reset()
    #         elif tool_or_other == ToolOrOther.CODER:
    #             code = None
    #             try:
    #                 code = coder.solve_intermediate(tool_prompt)
    #             except Exception as e:
    #                 self._log_and_add_to_history_buffer(f"Exception encountered in coder: {e}")
                
    #             if code is not None:
    #                 try:
    #                     output = executor.solve_intermediate(code) # TODO: maybe switch to multiple code generations and parallel execution

    #                     last_output, code_success = executor.extract_last_output(output)
    #                     if code_success:
    #                         self._log_and_add_to_history_buffer(f"Code executor output: {last_output}") # TODO: include entire code generated too?
    #                     else:
    #                         self._log_and_add_to_history_buffer(f"Code executor raised exception: {last_output}")
    #                 except Exception as e:
    #                     self._log_and_add_to_history_buffer(f"Exception encountered in code executor: {e}")
                
    #             coder.reset()
    #             executor.reset()
    #         elif tool_or_other == ToolOrOther.LLM_GUESSER:
    #             try:
    #                 guess = llm_guesser.solve_intermediate(tool_prompt)

    #                 self._log_and_add_to_history_buffer(f"LLM guesser guessed:\n{guess}")
    #             except Exception as e:
    #                 self._log_and_add_to_history_buffer(f"Exception encountered in LLM guesser: {e}")

    #             llm_guesser.reset()
    #         elif tool_or_other == ToolOrOther.PROVER:
    #             answer_error = False
    #             custom_proof_state_render = None
    #             if answer_temp is not None:
    #                 if problem_state == ProblemState.FINDING or problem_state == ProblemState.PROVING_AFTER_FINDING:
    #                     answer = answer_temp
    #                     if problem_state == ProblemState.FINDING:
    #                         answer_statement = f"Coordinator provided answer: {answer}"
    #                     else:
    #                         answer_statement = f"Coordinator provided new answer: {answer}"
    #                     self._log_and_add_to_history_buffer(answer_statement)

    #                     # TODO: deal with noncomputable real division? (only an issue if guess is fraction of real numbers but actual solution is literal)
    #                     formatted_answer = prover.solve_intermediate_format_answer(answer_statement, theorem_statement)
    #                     formatted_answer_statement = f"Prover formatted and inserted answer: {formatted_answer}"
    #                     self._log_and_add_to_history_buffer(formatted_answer_statement)
    #                     custom_proof_state_render = f"[MESSAGE]\n{formatted_answer_statement}\n[END]" # TODO: maybe move all this keyword formatting inside prover prompter

    #                     new_raw_theorem_statement = raw_theorem_statement.replace("sorry", formatted_answer, 1)
    #                     self.logger.info(f"Lean theorem with answer inserted:\n{new_raw_theorem_statement}")

    #                     theorem_statement = string_utils.filter_theorem_statement(new_raw_theorem_statement)
    #                     theorem_statement_statement = f"[LEAN 4 THEOREM STATEMENT]\n{theorem_statement}"
    #                     self._log_and_add_to_history_buffer(theorem_statement_statement)
    #                     custom_proof_state_render += f"\n\n{theorem_statement_statement}\n[END]"

    #                     temp_lean_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".lean")

    #                     temp_lean_file.write(new_raw_theorem_statement)
    #                     temp_lean_file.flush()

    #                     lean4_project_folder = proof_env_wrapper.proof_env.dynamic_proof_executor_callback.project_folder
    #                     temp_proof_env = proof_utils.get_proof_env(lean4_project_folder, temp_lean_file.name, name)
    #                     proof_env_wrapper.swap_proof_env(temp_proof_env, temp_lean_file)

    #                     problem_state = ProblemState.PROVING_AFTER_FINDING

    #                     proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env)
    #                     self._log_and_add_to_history_buffer(proof_state_render)
    #                     custom_proof_state_render += f"\n\n{proof_state_render}\n[END]"

    #                     rw_tactic = f"rw [{name}_solution]" # TODO: take solution name from theorem statement instead of hardcoding
    #                     rw_tactic_statement = f"Automatically executing tactic '{rw_tactic}' to rewrite the solution into the proof statement."
    #                     self._log_and_add_to_history_buffer(rw_tactic_statement)
    #                     custom_proof_state_render += f"\n\n[MESSAGE]\n{rw_tactic_statement}\n[END]"
    #                     action = ProofAction(ProofAction.ActionType.RUN_TACTIC, ProofAction.Language.LEAN4, tactics=[rw_tactic])
    #                     proof_env_wrapper.proof_env.step(action)

    #                     proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env)
    #                     self._log_and_add_to_history_buffer(proof_state_render)
    #                     custom_proof_state_render += f"\n\n{proof_state_render}"
    #                 else:
    #                     self._log_and_add_to_history_buffer(f"Exception: Providing an answer is invalid when the theorem doesn't require an answer to be inserted.")
    #                     answer_error = True
                
    #             if answer_error:
    #                 pass
    #             elif problem_state == ProblemState.PROVING or problem_state == ProblemState.PROVING_AFTER_FINDING:
    #                 try:
    #                     if custom_proof_state_render is not None:
    #                         proof_state_render = custom_proof_state_render
    #                     else:
    #                         proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env)
    #                     # a quick patch for a common formatting error # TODO: move this into coordinator prompter
    #                     answer_token_ind = tool_prompt.find("[ANSWER]")
    #                     if answer_token_ind != -1:
    #                         tool_prompt = tool_prompt[:answer_token_ind].strip()
    #                     tactic = prover.solve_intermediate(proof_state_render, tool_prompt)

    #                     tactic_list = tactic.split(";")
    #                     action = ProofAction(ProofAction.ActionType.RUN_TACTIC, ProofAction.Language.LEAN4, tactics=tactic_list)
    #                     proof_env_wrapper.proof_env.step(action)

    #                     proof_state_render = string_utils.render_proof_env(proof_env_wrapper.proof_env)
    #                     self._log_and_add_to_history_buffer(f"Prover generated and executed tactic.\n\n{proof_state_render}") # TODO: add this type of [TACTIC] keyword scaffolding to all other output messages (and exceptions?) ([TACTIC] no longer in this one)
    #                 except Exception as e:
    #                     self._log_and_add_to_history_buffer(f"Exception encountered in prover: {e}")
                    
    #                 if proof_env_wrapper.proof_env.done:
    #                     self.logger.info("Succesfully proved theorem, ending loop.")
    #                     end_loop = True
    #             else:
    #                 self._log_and_add_to_history_buffer("Exception: You must provide the prover a guess for the problem's answer.") # TODO: this won't be needed later?
    #         else:
    #             self._log_and_add_to_history_buffer(f"Exception: Coordinator-chosen tool '{tool_or_other}' is invalid.")

    #         time_left -= math.ceil(time.time() - start_time)
            
    #         self.logger.info(f"End of loop {loop_num}. Time left: {time_left} s\n") # TODO: let coordinator know time left?
        
    #     self.coordinator_history_logger.info(f"[PROBLEM] {name}")
    #     for message in coordinator.history:
    #         self.coordinator_history_logger.info(f"\n[ROLE] {message['role']}\n[CONTENT]\n{message['content']}")
    #     self.coordinator_history_logger.info("\n\n")

    #     coordinator.reset()
    #     prover.reset()

    #     self.logger.info("Solver finished looping.")

    #     if problem_state == ProblemState.FINDING:
    #         self.logger.info("Failed to provide answer.")
        
    #     if proof_env_wrapper.proof_env.done:
    #         self.logger.info("Succesfully proved theorem.")
    #     else:
    #         self.logger.info("Failed to prove theorem.")
        
    #     return answer, formatted_answer


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
