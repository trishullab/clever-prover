from itp_interface.rl.simple_proof_env import ProofEnv

def parse_float(input: str):
    try:
        return float(input)
    except:
        pass
    try:
        return eval(input)
    except:
        pass
    return None

def filter_theorem_statement(raw_theorem_statement: str) -> str:
    theorem_statement_lines = []
    for line in raw_theorem_statement.splitlines():
        if line and not line.isspace() and not line.startswith("import ") and not line.startswith("open ") and not line.startswith("--"):
            theorem_statement_lines.append(line)
    return "\n".join(theorem_statement_lines)

def history_to_str(history: list[dict[str, str]]) -> str:
    if len(history) > 10:
        return "[...,\n{}]".format(",\n".join(map(str, history[-10:]))) + "\n" + history[-1]["content"]
    else:
        return "[{}]".format(",\n".join(map(str, history))) + "\n" + history[-1]["content"]

def format_problem_statements(problem_statement: str, theorem_statement: str) -> str:
    return f"[PROBLEM STATEMENT]\n{problem_statement}\n\n[LEAN 4 THEOREM STATEMENT]\n{theorem_statement}"

def render_proof_env(proof_env: ProofEnv, solution_str: str) -> str:
    render_list = ["[PROOF STATE]"] # TODO: maybe remove [MESSAGE] that always appears before this
    goals_list = proof_env.state.training_data_format.start_goals
    for i in range(len(goals_list)):
        if i > 0:
            render_list.append("")
        goal = goals_list[i]
        render_list.extend(goal.hypotheses)
        render_list.append("⊢")
        render_list.append(goal.goal)
    if proof_env._history: # TODO: pass in info instead of taking from history
        _, _, _, _, _, info = proof_env._history[-1]
        render_list.append("")
        render_list.append(f"Info: {info.to_json()}")
    return "\n".join(render_list)

    # if len(proof_env._history) == 0:
    #     current_state = proof_env.state
    #     s_goals = [((f"Solution (Inserted): {solution_str}\n " if solution_str else "") +
    #                 f"Goal [{idx}]:\n {goal.goal}\n Hyps [{idx}]:\n {goal.hypotheses}\n Dfns [{idx}]:\n {goal.relevant_defns}\n Thms [{idx}]:\n {goal.possible_useful_theorems_local}\n------------------\n")
    #                 for idx, goal in enumerate(current_state.training_data_format.start_goals)]
    #     s_goal = '\n'.join(s_goals)
    #     return f"Proof State:\n {s_goal}"
    # render_list = []
    # s1, a, s2, r, d, info = proof_env._history[-1]
    # visibility = 3
    # # self.logger.info("-"*50)
    # # s1_relevant_dfns = [
    # #     "\n".join([str(s1.training_data_format.all_useful_defns_theorems[dfns.lemma_idx]) for dfns in goal.relevant_defns]) 
    # #         for goal in s1.training_data_format.start_goals]
    # # s1_possible_thms = [
    # #     "\n".join([str(s1.training_data_format.all_useful_defns_theorems[thm.lemma_idx]) 
    # #         for thm in (goal.possible_useful_theorems_local[:visibility] + goal.possible_useful_theorems_external[:visibility])])
    # #         for goal in s1.training_data_format.start_goals]
    # # s1_goals = [f"Goal [{idx}]:\n {goal.goal}\n Hyps [{idx}]:\n {goal.hypotheses}\n Dfns [{idx}]:\n {s1_relevant_dfns[idx]}\n Thms [{idx}]:\n {s1_possible_thms[idx]}\n------------------\n" for idx, goal in enumerate(s1.training_data_format.start_goals)]
    # # s1_goal = '\n'.join(s1_goals)
    # # self.logger.info(f"Proof State (before action):\n {s1_goal}")
    # s2_relevant_dfns = [
    #     "\n".join([str(s2.training_data_format.all_useful_defns_theorems[dfns.lemma_idx]) for dfns in goal.relevant_defns])
    #         for goal in s2.training_data_format.start_goals]
    # s2_possible_thms = [
    #     "\n".join([str(s2.training_data_format.all_useful_defns_theorems[thm.lemma_idx]) 
    #         for thm in (goal.possible_useful_theorems_local[:visibility] + goal.possible_useful_theorems_external[:visibility])])
    #         for goal in s2.training_data_format.start_goals]
    # s2_goals = [((f"Solution (Inserted): {solution_str}\n " if solution_str else "") +
    #                 f"Goal [{idx}]:\n {goal.goal}\n Hyps [{idx}]: {goal.hypotheses}\n Dfns [{idx}]:\n {s2_relevant_dfns[idx]}\n Thms [{idx}]:\n {s2_possible_thms[idx]}\n-------------------\n")
    #             for idx, goal in enumerate(s2.training_data_format.start_goals)] # TODO: convey solution another way? currently doesn't convey type, so maybe include entire line
    # action = a.serialize()
    # render_list.append(f"Action:\n {action}")
    # s2_goal = '\n'.join(s2_goals)
    # render_list.append(f"Proof State:\n {s2_goal}")
    # render_list.append(f"Reward:\n {r}")
    # render_list.append(f"Done:\n {d}")
    # render_list.append(f"Info:\n {info.to_json()}")
    # # self.logger.info("-"*50)
    # return "\n".join(render_list)
