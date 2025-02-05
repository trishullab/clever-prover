from aimo_gaz.prompters.prompter import Prompter

class CodePrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement with a corresponding formal theorem statement in Lean 4.

Can you write a Python program to help solve the problem using SymPy? The code can print a guess for the answer or some other helpful output. Make sure it runs correctly!

Please start the code with '```python' and end it with '```'""" # TODO: add examples
        self.problem_statement_message = "Problem Statement:\n{}\n\nLean 4 Theorem Statement:\n{}"
        self.default_user_message = "Please write the code now." # TODO: maybe adjust '```python' and '```' scaffolding
        
        self.stop_tokens = []

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, theorem_statement: str, tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
        problem_statements = self.problem_statement_message.format(problem_statement, theorem_statement)
        instructions = tool_prompt if tool_prompt else self.default_user_message
        history.append({"role": "user", "content": f"{problem_statements}\n\nInstructions:\n{instructions}"})
        return history

    def parse_response(self, response: str) -> str:
        actual_code_ind = response.find("```python")
        if actual_code_ind != -1:
            response = response[(actual_code_ind + len("```python")):]
        actual_code_ind = response.find("```")
        if actual_code_ind != -1:
            response = response[:actual_code_ind]
        return response.strip()
