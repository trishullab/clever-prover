from aimo_gaz.prompts.prompt import ConcatPrompt

class CodePrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt, append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """
Based on the procedure above, now let us write python code to solve the problem.
Make sure to print the final answer on a new line and end the code with the token [END CODE]."""
        self.assistant_message_start = """
```python code:
# [START CODE] Write your code here
"""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        if messages[-1]['role'] == 'user':
            messages[-1]['content'] += self.user_message
            messages.append({'role': 'assistant', 'content': self.assistant_message_start})
        return self.translate_for_deepseek(messages)

    def parse_response(self, response: str) -> str:
        return response