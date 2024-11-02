from aimo_gaz.prompts.prompt import ConcatPrompt

class CoordinatorPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is a math problem statement.

Problem Statement: {}

You are the coordinator in charge of solving this problem. You have several tools at your disposal to help you solve it. Your tools are:

(1) llm_guesser: Query an LLM to guess the answer to the problem.

Here is the history of actions taken so far by the coordinator (you) and the tools to solve this problem:

{}

Please output which tool you would like to use next."""

    def get_prompt(self, messages: list[dict[str, str]], history: list[str]) -> str:
        assert messages[-1]['role'] == 'user'
        messages[-1]['content'] = self.user_message.format(messages[-1]['content'], history) # TODO: format history better
        return messages

    def parse_response(self, response: str) -> str:
        if "llm_guesser" in response:
            return "llm_guesser"
        if "1" in response:
            return "llm_guesser"
        return None


if __name__ == "__main__":
    prompter = CoordinatorPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
