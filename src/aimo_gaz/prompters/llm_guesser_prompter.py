import typing
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.utils import string_utils

class LLMGuesserPrompter(Prompter):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

Please solve this problem and write for me a guess for the numerical answer to this problem, as an integer or a fraction.

Please start your guess with '[START GUESS]' and end it with '[END GUESS]'""" # TODO: add examples
        self.problem_statement_message = "Problem Statement: {}"
        self.user_message_with_plan = """Here are the first couple steps in trying to solve the problem:

First Couple Steps:
{}

Please write your guess now.""" # TODO: maybe find a better way to handle presence/absence of plan
        self.user_message_without_plan = "Please write your guess now."

        self.stop_tokens = ["[END GUESS]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str, plan: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        if plan is not None:
            history.append({"role": "user", "content": self.user_message_with_plan.format(plan)})
        else:
            history.append({"role": "user", "content": self.user_message_without_plan})
        return history

    def parse_response(self, response: str) -> typing.Tuple[str, float]:
        actual_guess_ind = response.rfind("[START GUESS]")
        if actual_guess_ind != -1:
            response = response[(actual_guess_ind + len("[START GUESS]")):]
        response = response.strip()

        guess_float = string_utils.parse_float(response)

        return response, guess_float


if __name__ == "__main__":
    prompter = LLMGuesserPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
