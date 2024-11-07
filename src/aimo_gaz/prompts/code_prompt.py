from aimo_gaz.prompts.prompt import ConcatPrompt
import copy

class CodePrompt(ConcatPrompt):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message_with_plan = """Below is a math problem statement and the first couple steps in trying to solve it.

Problem Statement: {}

First Couple Steps:
{}

Can you write a python program that tries to solve the problem statement using SymPy? The code should always answer by printing only a number (integer or fraction) and nothing else. Make sure it runs correctly!

Start the code with '```python' and end the code with '```'.""" # TODO: maybe find a better way to handle presence/absence of plan
        self.user_message_without_plan = """Below is a math problem statement.

Problem Statement: {}

Can you write a python program that tries to solve the problem statement using SymPy? The code should always answer by printing only a number (integer or fraction) and nothing else. Make sure it runs correctly!

Start the code with '```python' and end the code with '```'.""" # TODO: maybe adjust '```python' and '```' scaffolding

    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        assert messages[-2]['role'] == 'user'
        assert messages[-1]['role'] == 'user'
        messages_copy = copy.deepcopy(messages)
        messages.clear()
        if messages_copy[-1]["content"] is not None:
            messages.append({
                "role": "user",
                "content": self.user_message_with_plan.format(messages_copy[-2]['content'], messages_copy[-1]['content'])
            })
        else:
            messages.append({
                "role": "user",
                "content": self.user_message_without_plan.format(messages_copy[-2]['content'])
            })
        return messages

    def parse_response(self, response: str) -> str:
        actual_code_ind = response.find("```python")
        if actual_code_ind != -1:
            response = response[(actual_code_ind + len("```python")):]
        actual_code_ind = response.rfind("```")
        if actual_code_ind != -1:
            response = response[:actual_code_ind]
        return response.strip()
