from aimo_gaz.prompts.prompt import ConcatPrompt

class PlannerPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None,  append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt, append_system_prompt_after_every_message)
        self.system_prompt = """
Below is a math problem you are to solve. Give a high-level strategy for how to solve this problem, omitting any computations.
{}
"""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        return self.translate_for_deepseek(messages)
    
    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = PlannerPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"},
        {"role": "assistant", "content": "The sum of 2 and 2 is 4"},
        {"role": "user", "content": "What is the sum of 3 and 3?"},
        {"role": "assistant", "content": "The sum of 3 and 3 is"}
    ]))
