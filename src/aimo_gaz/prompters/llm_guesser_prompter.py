import re
import typing
from aimo_gaz.prompters.prompter import ConcatPrompter
from aimo_gaz.utils import string_utils

class LLMGuesserPrompter(ConcatPrompter):
    last_num_regex = re.compile(r"-?\d*\s*[./]?\s*\d+")

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

Problem Statement: {}

Write for me a guess for the numerical answer to this problem. Only output the guessed number, as an integer or a fraction."""
        self.user_message = """Please write your guess now.""" # TODO: add [START] and [END] scaffolding

    def get_prompt(self, history: list[dict[str, str]], problem_description: str) -> str:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt.format(problem_description)})
        history.append({"role": "user", "content": self.user_message})
        return history

    def parse_response(self, response: str) -> typing.Tuple[str, float]:
        guess_float = string_utils.parse_float(response)

        if guess_float is None: # TODO: this can be deleted once we add the [START] and [STOP] scaffolding
            guess_parse = self.last_num_regex.findall(response)
            if guess_parse:
                guess_float = string_utils.parse_float(guess_parse[-1])
                if guess_float is not None:
                    response = guess_parse[-1]

        return response.strip(), guess_float


if __name__ == "__main__":
    prompter = LLMGuesserPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
