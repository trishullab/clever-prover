# import typing
# from aimo_gaz.solver.abs_solver_and_tool import Tool
# from aimo_gaz.models.abs_model import Model
# from aimo_gaz.prompters.prompter import Prompter
# import logging

# class Lean4TacticTool(Tool):
#     def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
#         assert model is not None, "model must be provided."
#         assert prompter is not None, "prompter must be provided."
#         self.model = model
#         self.prompter = prompter
#         self.inference_kwargs = inference_kwargs
#         self.logger = logger
#         self.inference_kwargs["n"] = 1 # Only one response is needed from Lean 4 tactic tool
#         self.inference_kwargs["stop"] = []
#         self.history = []

#     def solve_intermediate(self, problem_description: str) -> typing.Tuple[str, float]:
#         if not self.model.is_loaded():
#             self.model.__enter__()
#         # Prompt the model for the plan
#         self.history = self.prompter.get_prompt(self.history, problem_description)
#         self.logger.info(f"[PLANNER] Raw prompt used:\n{self.history}")
#         # Get the model response
#         response = self.model.generate(self.history, **self.inference_kwargs)
#         outs = self.model.parse_out(response)
#         assert len(outs) == 1, "No response (or too many responses) from the model."
#         generated_text = outs[0][0]
#         self.history.append({"role": "assistant", "content": generated_text})
#         self.logger.info(f"[PLANNER] Plan generated.")
#         return f"{generated_text}"

#     def reset(self):
#         self.history = []

#     def __enter__(self):
#         self.model.__enter__()
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.model.__exit__(exc_type, exc_val, exc_tb)

# if __name__ == "__main__":
#     import sys
#     import os
#     root_dir = f"{__file__.split('src')[0]}"
#     if root_dir not in sys.path:
#         sys.path.append(root_dir)
#     os.chdir(root_dir)

#     from itp_interface.rl.simple_proof_env import ProofAction, ProofExecutorCallback, ProofEnvReRankStrategy, ProofEnv

#     # print("Interactive Proof Environment")
#     # supported_actions = [x.name for x in ProofAction.ActionType]

#     # def scan_action(language):
#     #     inp_action_type = input(f"Enter an action type from {supported_actions}: (default RUN_TACTIC)")
#     #     if inp_action_type not in supported_actions:
#     #         inp_action_type = ProofAction.ActionType.RUN_TACTIC.name
#     #     action_type = ProofAction.ActionType[inp_action_type]
#     #     if action_type == ProofAction.ActionType.RUN_TACTIC:
#     #         inp = input("Enter tactic(s) (';' separated): ")
#     #         inp = inp.split(';')
#     #         return ProofAction(action_type, language, tactics=inp)
#     #     elif action_type == ProofAction.ActionType.GET_DFNS_THMS or action_type == ProofAction.ActionType.BACKTRACK or action_type == ProofAction.ActionType.EXIT:
#     #         return ProofAction(action_type, language)
#     #     else:
#     #         raise Exception(f"Invalid action type {action_type}")

#     # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

#     # proof_exec_callback = ProofExecutorCallback(
#     #     project_folder="data/test/lean4_proj",
#     #     file_path="data/test/lean4_proj/Lean4Proj/Basic.lean",
#     #     language=ProofAction.Language.LEAN4,
#     #     always_use_retrieval=False,
#     #     keep_local_context=True
#     # )
#     # theorem_name = "test3"
#     # language = ProofAction.Language.LEAN4
#     # always_retrieve_thms = False
#     # retrieval_strategy = ProofEnvReRankStrategy.NO_RE_RANK
    
#     # with ProofEnv("test", proof_exec_callback, theorem_name, retrieval_strategy=retrieval_strategy, max_proof_depth=10, always_retrieve_thms=always_retrieve_thms) as env:
#     #     done = env.done
#     #     action = scan_action(language)
#     #     while action.action_type != ProofAction.ActionType.EXIT and not done:
#     #         state, _, _, reward, done, info = env.step(action)
#     #         env.render()
#     #         if not done:
#     #             action = scan_action(language)
