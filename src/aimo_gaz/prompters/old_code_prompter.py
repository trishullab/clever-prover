from aimo_gaz.prompters.prompter import Prompter
import copy

class OldCodePrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list, append_system_prompt_after_every_message)
#         self.user_message = """Below is a problem statement and the first couple steps in trying to solve it. Can you write a python program that tries to solve the problem statement using SymPy? The code should always answer with a number. Make sure it runs correctly! End the code by writing [END CODE].\n\nProblem Statement:
# {}
# First Couple Steps:
# 1. {}
# """
        self.user_message = """Below is a problem statement and the first couple steps in trying to solve it. Can you write a python program that tries to solve the problem statement using SymPy? The code should always answer by printing only a number (integer or fraction) and nothing else. Make sure it runs correctly! End the code by writing [END CODE].

Problem Statement:
{}
First Couple Steps:
1. {}
"""
#         self.user_message = """Below is the math problem you must solve:
# {}
# And here is a possible procedure for solving it:
# {}
# Solve the problem by writing a python program that uses sympy which computes the final answer. You can use the procedure above if you think it is useful. Do NOT copy it directly into your program.
# Make sure to print the final answer on a new line using print command. End the code by writing [END CODE]."""
        self.assistant_message_start = """```python
"""
    def get_prompt(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        if history[-1]['role'] == 'assistant': # already have information produced
            history.append({'role': 'user', 'content': self.user_message})
            history.append({'role': 'assistant', 'content': self.assistant_message_start}) # TODO: Do this in a more natural way?
        if history[-1]['role'] == 'user': # fresh sample, not using history from other solvers
            history_copy = copy.deepcopy(history)
            history.clear()
            history.append({
                'role': 'user',
                'content': self.user_message.format(history_copy[-2]['content'], history_copy[-1]['content'])
            })
            history.append({'role': 'assistant', 'content': self.assistant_message_start})
        # return self.translate_for_deepseek(history, no_newline_after_assistant=True)
        return history

    def parse_response(self, response: str) -> str:
        return response
