from aimo_gaz.prompts.prompt import ConcatPrompt

class PlannerPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt)
        self.system_prompt = """
Problem: For how many positive integers $m$ does the equation $||x-1|-2|=m/100$ have $4$ distinct solutions?	
[START PROCEDURE]
Procedure:
1. Solve for the solution set of $||x-1|-2|=m/100$ where $m$ is a positive integer.
2. Count the number of choices of $m$ where the solution set has 4 elements.
[END PROCEDURE]

Give a BRIEF procedure, in the form of a SHORT list, that lists the intermediate subgoals that should be performed using sympy, NOT YOU, to solve this problem. Do NOT try to solve the problem, do NOT include any computations or choices. Write [END PROCEDURE] when you have finished the list. An example was included above.

Below is the math problem you are to solve. 
Problem: {}
[START PROCEDURE]
Procedure:
1."""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        message = list(messages[0].values())[0]
        full_prompt = self.system_prompt.format(message)
        return full_prompt
    
    def parse_response(self, response: str) -> str:
        return response