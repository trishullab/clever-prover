import typing
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.utils import string_utils

class LLMGuesserPrompter(Prompter):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

Please write for me a guess for a numerical answer to help solve this problem, as an integer or a fraction.

Please start your guess with '[START GUESS]' and end it with '[END GUESS]'""" # TODO: add examples # TODO: remove restriction on only printing a number
        self.problem_statement_message = "Problem Statement: {}" # TODO: phrase this as a helper instead of a guesser
        self.default_user_message = "Please write your guess now."

        self.stop_tokens = ["[END GUESS]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str, tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": tool_prompt if tool_prompt else self.default_user_message})
        return history

    def parse_response(self, response: str) -> typing.Tuple[str, float]:
        actual_guess_ind = response.rfind("[START GUESS]")
        if actual_guess_ind != -1:
            response = response[(actual_guess_ind + len("[START GUESS]")):]
        return response.strip()


if __name__ == "__main__":
    prompter = LLMGuesserPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
