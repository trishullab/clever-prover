from itp_interface.rl.simple_proof_env import ProofEnv
from aimo_gaz.prompters.prompter import Prompter

class ProverPrompter(Prompter):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is the informal problem statement and current proof state of a theorem in Lean 4, along with the history of proof states and tactics used to prove it.

Please write for me the next tactic to prove this theorem in Lean 4. Only write one tactic.

Be sure to use correct Lean 4 notation.

Please start your response with '[START TACTIC]' and end it with '[END TACTIC]'""" # TODO: add examples
        self.problem_statement_message = "Problem Statement: {}"
        self.user_message = "Please write the next tactic now."
        
        self.stop_tokens = ["[END TACTIC]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": self.user_message})
        return history

    def parse_response(self, response: str) -> str:
        actual_tactic_ind = response.rfind("[START TACTIC]")
        if actual_tactic_ind != -1:
            response = response[(actual_tactic_ind + len("[START TACTIC]")):]
        return response.strip()

    def render_proof_env(self, proof_env: ProofEnv):
        if len(proof_env._history) == 0:
            current_state = proof_env.state
            s_goals = [f"Goal [{idx}]:\n {goal.goal} \n Hyps [{idx}]:\n {goal.hypotheses} \n Dfns [{idx}]:\n {goal.relevant_defns} \n Thms [{idx}]:\n {goal.possible_useful_theorems_local} \n------------------\n" for idx, goal in enumerate(current_state.training_data_format.start_goals)]
            s_goal = '\n'.join(s_goals)
            return f"Proof State:\n {s_goal}"
        render_list = []
        s1, a, s2, r, d, info = proof_env._history[-1]
        visibility = 3
        # self.logger.info("-"*50)
        # s1_relevant_dfns = [
        #     "\n".join([str(s1.training_data_format.all_useful_defns_theorems[dfns.lemma_idx]) for dfns in goal.relevant_defns]) 
        # for goal in s1.training_data_format.start_goals]
        # s1_possible_thms = [
        #         "\n".join([str(s1.training_data_format.all_useful_defns_theorems[thm.lemma_idx]) 
        #     for thm in (goal.possible_useful_theorems_local[:visibility] + goal.possible_useful_theorems_external[:visibility])])
        # for goal in s1.training_data_format.start_goals]
        # s1_goals = [f"Goal [{idx}]:\n {goal.goal} \n Hyps [{idx}]:\n {goal.hypotheses} \n Dfns [{idx}]:\n {s1_relevant_dfns[idx]} \n Thms [{idx}]:\n {s1_possible_thms[idx]} \n------------------\n" for idx, goal in enumerate(s1.training_data_format.start_goals)]
        # s1_goal = '\n'.join(s1_goals)
        # self.logger.info(f"Proof State (before action):\n {s1_goal}")
        s2_relevant_dfns = [
            "\n".join([str(s2.training_data_format.all_useful_defns_theorems[dfns.lemma_idx]) for dfns in goal.relevant_defns])
        for goal in s2.training_data_format.start_goals]
        s2_possible_thms = [
                "\n".join([str(s2.training_data_format.all_useful_defns_theorems[thm.lemma_idx]) 
            for thm in (goal.possible_useful_theorems_local[:visibility] + goal.possible_useful_theorems_external[:visibility])])
        for goal in s2.training_data_format.start_goals]
        s2_goals = [f"Goal [{idx}]:\n {goal.goal} \n Hyps [{idx}]: {goal.hypotheses} \n Dfns [{idx}]:\n {s2_relevant_dfns[idx]} \n Thms [{idx}]:\n {s2_possible_thms[idx]} \n-------------------\n" for idx, goal in enumerate(s2.training_data_format.start_goals)]
        action = a.serialize()
        render_list.append(f"Action:\n {action}")
        s2_goal = '\n'.join(s2_goals)
        render_list.append(f"Proof State:\n {s2_goal}")
        render_list.append(f"Reward:\n {r}")
        render_list.append(f"Done:\n {d}")
        render_list.append(f"Info:\n {info.to_json()}")
        # self.logger.info("-"*50)
        return "\n".join(render_list)
