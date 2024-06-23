from aimo_gaz.prompts.prompt import ConcatPrompt
import copy

class CodePrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt, append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is the math problem you must solve:
{}
And here is a possible procedure for solving it:
{}         
Solve the problem by writing a python program that uses sympy which computes the final answer. You can use the procedure above if you think it is useful. Do NOT copy it directly into your program.
Make sure to print the final answer on a new line using print command. End the code by writing [END CODE]."""
        self.assistant_message_start = """```python code:
"""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        if messages[-1]['role'] == 'assistant': # already have information produced
            messages.append({'role': 'user', 'content': self.user_message})
            messages.append({'role': 'assistant', 'content': self.assistant_message_start})
        if messages[-1]['role'] == 'user': # fresh sample, not using history from other solvers
            messages_copy = copy.deepcopy(messages)
            messages.clear()
            messages.append({
                'role': 'user', 
                'content': self.user_message.format(messages_copy[-2]['content'], messages_copy[-1]['content'])
            })
            messages.append({'role': 'assistant', 'content': self.assistant_message_start})
        return self.translate_for_deepseek(messages, no_newline_after_assistant=True)

    def parse_response(self, response: str) -> str:
        return response