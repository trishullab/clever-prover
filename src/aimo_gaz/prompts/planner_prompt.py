from aimo_gaz.prompts.prompt import ConcatPrompt

class PlannerPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt)
        self.system_prompt = """
Below is a math problem you are to solve. Give a high-level strategy for how to solve this problem, omitting any computations.
{}
"""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        message = list(messages[0].values())[0]
        full_prompt = self.system_prompt.format(message)
        return full_prompt
    
    def parse_response(self, response: str) -> str:
        return response