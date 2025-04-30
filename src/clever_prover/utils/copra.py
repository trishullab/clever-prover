import logging
import typing
import time
from itp_interface.rl.simple_proof_env import ProofSearchResult, ProofExecutorCallback, ProofAction
from copra.agent.dfs_tree_search_with_stack import DFSTreeSearch
from copra.agent.dfs_policy_prompter import DfsCoqGptPolicyPrompter, InformalProofRepo
from copra.agent.gpt_guided_tree_search_policy import GptGuidedTreeSearchPolicy
from copra.agent.simple_proof_agent import ProofAgent, ProofEnv

class TempInformalProofRepo(InformalProofRepo):
    def __init__(self, theorem_name: str, informal_problem: str, informal_hint: str):
        super().__init__()
        self.theorem_name = theorem_name
        self.informal_problem = informal_problem
        self.informal_hint = informal_hint

    def informal_proof_exists(self, theorem_name: str) -> bool:
        return theorem_name == self.theorem_name
    
    def get_informal_thm_proof(self, theorem_name: str) -> typing.Tuple[str, str]:
        assert theorem_name == self.theorem_name, f"{theorem_name} != {self.theorem_name}"
        return (self.informal_problem, self.informal_hint)


def get_proof_via_copra(
    project_path: str,
    file_path: str,
    lemma_name: str,
    informal_problem: str,
    informal_hints: str,
    timeout_in_ms: int,
    proof_dump_file_path: str,
    system_prompt: str = None,
    example_prompt: str = None,
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_history_messages: int = 0,
    secret_filepath: str = ".secrets/openai_key.json",
    max_tokens_per_action: int = 1000,
    logger: logging.Logger = None) -> ProofSearchResult:
    proof_exec_callback = ProofExecutorCallback(
        project_folder=project_path,
        file_path=file_path,
        language=ProofAction.Language.LEAN4,
        timeout_in_secs=60,
        keep_local_context=True
    )
    informal_repo = TempInformalProofRepo(
        theorem_name=lemma_name,
        informal_problem=informal_problem,
        informal_hint=informal_hints
    )
    policy_prompter = DfsCoqGptPolicyPrompter(
        main_sys_prompt_path=system_prompt,
        example_conv_prompt_path=example_prompt,
        temperature=temperature,
        max_tokens_per_action=max_tokens_per_action,
        gpt_model_name=model_name,
        secret_filepath=secret_filepath,
        lemma_name=lemma_name,
        informal_proof_repo=informal_repo,
        language=ProofAction.Language.LEAN4,
        max_history_messages=max_history_messages,
        retrieve_prompt_examples=False,
        logger=logger)
    search_algorithm = DFSTreeSearch(language=ProofAction.Language.LEAN4)
    search_policy = GptGuidedTreeSearchPolicy(
        checkpoint_dir='',
        checkpoint_filename='',
        policy_prompter=policy_prompter,
        tree_search_algorithm=search_algorithm,
        checkpoint_on_exit=False,
        language=ProofAction.Language.LEAN4
    )
    proof_env = ProofEnv(
        f"ProofEnv-{lemma_name}",
        proof_exec_callback,
        lemma_name,
        max_proof_depth=300,
        logger=logger
    )
    start_time = time.time()
    def _stop_policy(*args, **kwargs) -> bool:
        elapsed_time = time.time() - start_time
        elapsed_time_in_ms = elapsed_time * 1000
        if elapsed_time_in_ms > timeout_in_ms:
            logger.info(f"Timeout reached: {elapsed_time_in_ms} ms")
            return True
        return False
    
    def _policy_info_message(*args, **kwargs) -> str:
        elapsed_time = time.time() - start_time
        remaining_time = timeout_in_ms - (elapsed_time * 1000)
        return f"Remaining search time: {remaining_time} ms"

    with proof_env:
        with search_policy:
            proof_agent = ProofAgent(
                name=f"ProofAgent-{lemma_name}",
                policy=search_policy,
                proof_dump_file_name=proof_dump_file_path,
                logger=logger,
            )
            proof_agent.run_episodes_till_stop(
                env=proof_env,
                render=False,
                episodes=1,
                stop_policy=_stop_policy,
                policy_info_message=_policy_info_message
            )
            elapsed_time = time.time() - start_time
            if hasattr(proof_env, "proof_search_res"):
                proof_search_res = proof_env.proof_search_res
                proof_search_res.proof_file = file_path
                proof_search_res.proof_time_in_secs = elapsed_time
                proof_search_res.is_timeout = elapsed_time * 1000 > timeout_in_ms
                return proof_env.proof_search_res
            else:
                return ProofSearchResult(
                    proof_file=file_path,
                    proof_found=False,
                    lemma_name=lemma_name,
                    proof_steps=[],
                    proof_time_in_secs=elapsed_time,
                    inferences_taken=-1,
                    possible_failed_paths=-1,
                    possible_failed_paths_count=-1,
                    num_of_backtracks=-1,
                    is_timeout=elapsed_time * 1000 > timeout_in_ms,
                    is_inference_exhausted=False,
                    longest_success_path=-1,
                    language=ProofAction.Language.LEAN4
                )