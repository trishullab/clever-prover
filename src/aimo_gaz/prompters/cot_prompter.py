import re
from aimo_gaz.prompters.prompter import ConcatPrompter

class CoTPrompter(ConcatPrompter):
    int_regex = re.compile(r"[-+]?\d+")
    box_regex = re.compile(r"\\boxed{([-+]?\d+)}")

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None,  append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt, append_system_prompt_after_every_message)
        self.system_prompt = """
Below is a math problem you are to solve (positive numerical answer!):
\"{}\"
Analyze this problem and think step by step to come to a solution with programs. After solving the problem, output the final numerical answer within \\boxed{}.
Once you found the answer write [END] and stop the response.\n\n
Please reason step by step, and put your final answer within \\boxed{}.\n\n
"""

    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        # return self.translate_for_deepseek(messages)
        return messages
    
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
