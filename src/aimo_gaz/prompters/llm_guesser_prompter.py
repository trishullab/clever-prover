import typing
from aimo_gaz.prompters.prompter import Prompter

class LLMGuesserPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement with a corresponding formal theorem statement in Lean 4.

Please write for me a guess for an answer to help solve this problem.""" # TODO: add examples
        self.problem_statement_message = "Problem Statement:\n{}\n\nLean 4 Theorem Statement:\n{}" # TODO: phrase this as a helper instead of a guesser
        self.default_user_message = "Please write your guess now."

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, theorem_statement: str, tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_statement, theorem_statement)})
        history.append({"role": "user", "content": tool_prompt if tool_prompt else self.default_user_message})
        return history

    def parse_response(self, response: str) -> typing.Tuple[str, float]:
        return response.strip()


if __name__ == "__main__":
    prompter = LLMGuesserPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
