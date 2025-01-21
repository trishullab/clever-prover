import typing
from itp_interface.rl.simple_proof_env import ProofAction, ProofEnv
from aimo_gaz.solver.abs_solver_and_tool import Tool
from aimo_gaz.models.abs_model import Model
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.utils import string_utils
import logging
import hydra

class ProverTool(Tool): # TODO: ignoring all actions other than RUN_TACTIC for now
    def __init__(self, model: Model, prompter: Prompter, logger: logging.Logger = None, **inference_kwargs):
        assert model is not None, "model must be provided."
        assert prompter is not None, "prompter must be provided."
        self.model = model
        self.prompter = prompter
        self.inference_kwargs = inference_kwargs
        self.logger = logger
        self.inference_kwargs["n"] = 1 # Only one response is needed from prover tool
        self.inference_kwargs["stop"] = prompter.stop_tokens
        self.history = []

    def solve_intermediate(self, problem_description: str, proof_env: ProofEnv, solution_str: str) -> typing.Tuple[str, float]: # TODO: maybe make solution_str part of proof_env instead of passing it separately
        if not self.model.is_loaded():
            self.model.__enter__()
        # Prompt the model for the tactic
        self.history = self.prompter.get_prompt(self.history, problem_description, proof_env, solution_str)
        self.logger.info(f"[PROVER] Raw prompt used:\n{string_utils.history_to_str(self.history)}")
        # Get the model response
        response = self.model.generate(self.history, **self.inference_kwargs)
        outs = self.model.parse_out(response)
        assert len(outs) == 1, "No response (or too many responses) from the model."
        generated_text = outs[0][0]
        self.history.append({"role": "assistant", "content": generated_text})
        self.logger.info(f"[PROVER] Tactic generated: {generated_text}")
        tactic = self.prompter.parse_response(generated_text)

        tactic_list = tactic.split(";")
        action = ProofAction(ProofAction.ActionType.RUN_TACTIC, ProofAction.Language.LEAN4, tactics=tactic_list)
        proof_env.step(action)

        proof_state_render = self.prompter.render_proof_env(proof_env, solution_str)
        return tactic, proof_state_render

    def reset(self):
        self.history = []

    def __enter__(self):
        self.model.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.model.__exit__(exc_type, exc_val, exc_tb)


@hydra.main(config_path="../../configs/", config_name="prover_tool_config", version_base="1.2")
def main(cfg):
    import sys
    import os
    from aimo_gaz.solver.solver_and_tool_config import parse_solver_or_tool_config
    from itp_interface.rl.simple_proof_env import ProofExecutorCallback, ProofEnvReRankStrategy

    print("Interactive Proof Environment")
    supported_actions = [x.name for x in ProofAction.ActionType]

    # def scan_action(language):
    #     inp_action_type = input(f"Enter an action type from {supported_actions}: (default RUN_TACTIC)")
    #     if inp_action_type not in supported_actions:
    #         inp_action_type = ProofAction.ActionType.RUN_TACTIC.name
    #     action_type = ProofAction.ActionType[inp_action_type]
    #     if action_type == ProofAction.ActionType.RUN_TACTIC:
    #         inp = input("Enter tactic(s) (';' separated): ")
    #         inp = inp.split(';')
    #         return ProofAction(action_type, language, tactics=inp)
    #     elif action_type == ProofAction.ActionType.GET_DFNS_THMS or action_type == ProofAction.ActionType.BACKTRACK or action_type == ProofAction.ActionType.EXIT:
    #         return ProofAction(action_type, language)
    #     else:
    #         raise Exception(f"Invalid action type {action_type}")

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    proof_exec_callback = ProofExecutorCallback(
        project_folder="../../data/test/lean4_proj",
        file_path="../../data/test/lean4_proj/Lean4Proj/Basic.lean",
        language=ProofAction.Language.LEAN4,
        always_use_retrieval=False,
        keep_local_context=True
    )
    theorem_name = "test3"
    language = ProofAction.Language.LEAN4
    always_retrieve_thms = False
    retrieval_strategy = ProofEnvReRankStrategy.NO_RE_RANK

    # with ProofEnv("test", proof_exec_callback, theorem_name, retrieval_strategy=retrieval_strategy, max_proof_depth=10, always_retrieve_thms=always_retrieve_thms) as env:
    #     done = env.done
    #     env.render()
    #     action = scan_action(language)
    #     while action.action_type != ProofAction.ActionType.EXIT and not done:
    #         state, _, _, reward, done, info = env.step(action)
    #         env.render()
    #         if not done:
    #             action = scan_action(language)

    dirpath = os.path.abspath(os.path.join(__file__, f"{os.pardir}/{os.pardir}/{os.pardir}/"))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.chdir(dirpath)
    logger = logging.getLogger(__name__)
    solver_config = parse_solver_or_tool_config(cfg)
    prover = solver_config.get_solver_or_tool(logger)

    with ProofEnv("test", proof_exec_callback, theorem_name, retrieval_strategy=retrieval_strategy, max_proof_depth=10, always_retrieve_thms=always_retrieve_thms) as env:
        env.render()
        while not env.done:
            input("Press enter: ")
            prover.solve_intermediate("", env)
            env.render()

if __name__ == "__main__":
    main()
