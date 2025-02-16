from aimo_gaz.prompters.prompter import Prompter

class CoordinatorFormatAnswerPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.user_instructions = """[INSTRUCTIONS]
You have output your guess for the answer to this problem, but it may not yet be in the proper Lean 4 format to insert into the Lean 4 theorem statement.

[LEAN 4 THEOREM STATEMENT]
{}

[INSTRUCTIONS]
Please format your guessed answer in Lean 4 notation to replace the first 'sorry' in the Lean 4 theorem statement above. Output your formatted answer between the tokens '[START FORMATTED ANSWER]' and '[END FORMATTED ANSWER]'"""

        self.stop_tokens = ["[END FORMATTED ANSWER]"]

    def get_prompt(self, history: list[dict[str, str]], history_buffer: list[str], theorem_statement: str) -> list[dict[str, str]]:
        user_message = ""

        if history_buffer:
            user_message += "[MESSAGE]\n" + "\n\n[MESSAGE]\n".join(history_buffer) + "\n\n"

        user_message += self.user_instructions.format(theorem_statement)

        history.append({"role": "user", "content": user_message})

        return history

    def parse_response(self, response: str) -> str:
        actual_formatted_answer_ind = response.rfind("[START FORMATTED ANSWER]")
        if actual_formatted_answer_ind != -1:
            response = response[(actual_formatted_answer_ind + len("[START FORMATTED ANSWER]")):]
        return response.strip()
