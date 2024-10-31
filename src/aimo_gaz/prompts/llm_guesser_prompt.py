from aimo_gaz.prompts.prompt import ConcatPrompt

class LLMGuesserPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is a math problem statement. Write for me a guess for the numerical answer to this problem. Only output the guessed number, as an integer or a fraction.\n\nProblem Statement: {}"""

    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        assert messages[-1]['role'] == 'user'
        messages[-1]['content'] = self.user_message.format(messages[-1]['content'])
        return messages

    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = LLMGuesserPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
