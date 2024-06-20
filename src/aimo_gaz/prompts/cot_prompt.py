import re
from aimo_gaz.prompts.prompt import ConcatPrompt

class CoTPrompt(ConcatPrompt):
    int_regex = re.compile(r"[-+]?\d+")
    box_regex = re.compile(r"\\boxed{([-+]?\d+)}")
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt)
        self.system_prompt = """
Below is a math problem you are to solve (positive numerical answer!):
\"{}\"
Analyze this problem and think step by step to come to a solution with programs. After solving the problem, output the final numerical answer within \\boxed{}.
Once you found the answer write [END] and stop the response.\n\n
"""
    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        message = list(messages[0].values())[0]
        full_prompt = self.system_prompt.format(message, '{}')
        return full_prompt
    
    # def parse_response(self, response: str) -> str:
    #     # Find the [ANSWER] keyword in the response
    #     start_idx = response.find("[ANSWER]")
    #     if start_idx == -1:
    #         return "No answer found."
    #     # Find the end of the answer
    #     end_idx = response.find("[END]", start_idx)
    #     if end_idx == -1:
    #         return "No end of answer found."
    #     # Extract the answer
    #     answer = response[start_idx + len("[ANSWER]"):end_idx]
    #     answer = answer.strip()
    #     return answer

    def parse_response(self, response: str) -> str:
        boxed_matches = self.box_regex.findall(response)
        last_match = boxed_matches[-1] if boxed_matches else None
        answer = last_match
        if last_match is None:
            # Return the last integer in the response
            match = self.int_regex.findall(response)
            if match:
                answer = match[-1]
            else:
                answer = "No answer found."
        # Extract the answer
        answer = answer.strip()
        return answer
