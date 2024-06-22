from aimo_gaz.prompts.prompt import ConcatPrompt

class PlannerPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None, example_prompt: str = None,  append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt, append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_messages = [
"""
Give a BRIEF high-level procedure, in the form of a SHORT list, that lists the intermediate subgoals that should be performed using sympy, NOT YOU, to solve this problem. Do NOT try to solve the problem, do NOT include any computations or choices. Write [END PROCEDURE] when you have finished the list. An example is shown below.
Problem: For how many positive integers $m$ does the equation $||x-1|-2|=m/100$ have $4$ distinct solutions?""",
"""
User:
Below is the math problem you are to solve. Please describe a high-level procedure to solve the problem.
Problem: {}
"""
        ]
        self.assistant_message_starts = [
"""
[START PROCEDURE]
Procedure:
1. Solve for the solution set of $||x-1|-2|=m/100$ where $m$ is a positive integer.
2. Count the number of choices of $m$ where the solution set has 4 elements.
[END PROCEDURE]
""",
"""
[START PROCEDURE]
Procedure:
1."""
        ]

    def get_prompt(self, messages: list[dict[str, str]]) -> str:
        if messages[-1]['role'] == 'user':
            main_message_added = False
            for msg in messages:
                if msg['role'] == 'user' and msg['content'] == self.user_messages[0]:
                    main_message_added = True
                    break
            if not main_message_added:
                messages = [
                {'role': 'user', 'content': self.user_messages[0]}, 
                {'role': 'assistant', 'content': self.assistant_message_starts[0]}
                ] + messages
            messages[-1]['content'] = self.user_messages[1].format(messages[-1]['content'])
            messages.append({'role': 'assistant', 'content': self.assistant_message_starts[1]})
        return self.translate_for_deepseek(messages)
    
    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = PlannerPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"},
        # {"role": "assistant", "content": "The sum of 2 and 2 is 4"},
        # {"role": "user", "content": "What is the sum of 3 and 3?"},
        # {"role": "assistant", "content": "The sum of 3 and 3 is"}
    ]))
