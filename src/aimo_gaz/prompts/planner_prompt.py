from aimo_gaz.prompts.prompt import ConcatPrompt

class PlannerPrompt(ConcatPrompt):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is a math problem statement.

Problem Statement: {}

Write for me the first couple steps you would do to solve this problem.  Only write the first couple steps please.""" # TODO: add [START] and [END] scaffolding

    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        assert messages[-1]['role'] == 'user'
        messages[-1]['content'] = self.user_message.format(messages[-1]['content'])
        return messages

    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = PlannerPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
