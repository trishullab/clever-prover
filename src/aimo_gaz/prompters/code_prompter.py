from aimo_gaz.prompters.prompter import Prompter

class CodePrompter(Prompter):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

Problem Statement: {}

Can you write a python program that tries to solve the problem statement using SymPy? The code should always answer by printing only a number (integer or fraction) and nothing else. Make sure it runs correctly!

Please start the code with '```python' and end it with '```'""" # TODO: add examples
        self.user_message_with_plan = """Here are the first couple steps in trying to solve the problem:

First Couple Steps:
{}

Please write the code now.""" # TODO: maybe find a better way to handle presence/absence of plan
        self.user_message_without_plan = """Please write the code now.""" # TODO: maybe adjust '```python' and '```' scaffolding

    def get_prompt(self, history: list[dict[str, str]], problem_description: str, plan: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt.format(problem_description)})
        if plan is not None:
            history.append({"role": "user", "content": self.user_message_with_plan.format(plan)})
        else:
            history.append({"role": "user", "content": self.user_message_without_plan})
        return history

    def parse_response(self, response: str) -> str:
        actual_code_ind = response.find("```python")
        if actual_code_ind != -1:
            response = response[(actual_code_ind + len("```python")):]
        actual_code_ind = response.rfind("```")
        if actual_code_ind != -1:
            response = response[:actual_code_ind]
        return response.strip()
