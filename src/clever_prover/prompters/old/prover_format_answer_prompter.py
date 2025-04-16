from clever_prover.prompters.prompter import Prompter

class ProverFormatAnswerPrompter(Prompter): # TODO: rename to prover
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        self.theorem_statement_statement = """[LEAN 4 THEOREM STATEMENT]
{}
[END]"""
        self.user_instructions = """[INSTRUCTIONS]
A coordinator has provided its guess for the answer to this problem, but it may not yet be in the proper Lean 4 format to insert into the Lean 4 theorem statement. Please format your guessed answer in Lean 4 notation to replace the first 'sorry' in the Lean 4 theorem statement above. Output your formatted answer between the keywords '[FORMATTED ANSWER]' and '[END]'
[END]"""

        self.stop_tokens = ["[END]"]

    def get_prompt(self, history: list[dict[str, str]], answer_statement: str, theorem_statement: str) -> list[dict[str, str]]:
        user_message = f"[MESSAGE]\n{answer_statement}\n[END]"
        user_message += "\n\n" + self.theorem_statement_statement.format(theorem_statement)
        user_message += "\n\n" + self.user_instructions

        history.append({"role": "user", "content": user_message})

        return history

    def parse_response(self, response: str) -> str:
        actual_formatted_answer_ind = response.rfind("[FORMATTED ANSWER]")
        if actual_formatted_answer_ind != -1:
            response = response[(actual_formatted_answer_ind + len("[FORMATTED ANSWER]")):]
        return response.strip()
