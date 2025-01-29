from aimo_gaz.prompters.prompter import Prompter

class ProverPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is the informal problem statement and current proof state of a theorem in Lean 4.

Please write for me the next tactic to prove this theorem in Lean 4. Only write one tactic.

Be sure to use correct Lean 4 notation; do not use Lean 3 notation.

Please start your response with '[START TACTIC]' and end it with '[END TACTIC]'""" # TODO: add examples
        self.problem_statement_message = "Problem Statement:\n{}"
        self.default_user_message = "Please write the next tactic now."
        
        self.stop_tokens = ["[END TACTIC]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str, proof_state_render: str, tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": proof_state_render})
        history.append({"role": "user", "content": tool_prompt if tool_prompt else self.default_user_message})
        return history

    def parse_response(self, response: str) -> str:
        actual_tactic_ind = response.rfind("[START TACTIC]")
        if actual_tactic_ind != -1:
            response = response[(actual_tactic_ind + len("[START TACTIC]")):]
        return response.strip()
