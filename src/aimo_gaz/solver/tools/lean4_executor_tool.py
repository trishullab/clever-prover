from itp_interface.rl.simple_proof_env import ProofEnv, ProofAction
from aimo_gaz.solver.abs_solver_and_tool import Tool
import logging
import hydra

class Lean4ExecutorTool(Tool):
    def __init__(self, logger: logging.Logger = None):
        assert logger is not None, "Logger must be provided."
        self.logger = logger
        self.history = []

    def solve_intermediate(self, proof_env: ProofEnv, tactic: str):
        tactic_list = tactic.split(";")
        action = ProofAction(ProofAction.ActionType.RUN_TACTIC, ProofAction.Language.LEAN4, tactics=tactic_list)
        proof_env.step(action)

        self.logger.info(f"[LEAN 4 EXECUTOR] Tactic executed.")

    def reset(self):
        self.history = []

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


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
