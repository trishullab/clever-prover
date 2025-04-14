from itp_interface.rl.simple_proof_env import ProofExecutorCallback, ProofAction, ProofEnvReRankStrategy, ProofEnv

def get_proof_env(lean4_project_folder: str, theorem_file_path: str, name: str) -> ProofEnv:
    proof_exec_callback = ProofExecutorCallback(
        project_folder=lean4_project_folder,
        file_path=theorem_file_path,
        language=ProofAction.Language.LEAN4,
        always_use_retrieval=False,
        keep_local_context=True
    )
    theorem_name = name
    always_retrieve_thms = False
    retrieval_strategy = ProofEnvReRankStrategy.NO_RE_RANK

    return ProofEnv(name, proof_exec_callback, theorem_name, retrieval_strategy=retrieval_strategy, max_proof_depth=10, always_retrieve_thms=always_retrieve_thms)
