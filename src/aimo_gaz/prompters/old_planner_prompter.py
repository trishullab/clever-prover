from aimo_gaz.prompters.prompter import ConcatPrompter
import copy

class OldPlannerPrompter(ConcatPrompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_messages = ['',
                              """Below is a problem statement. Write for me the first couple steps you would do to solve this problem.  Only write the first couple steps please.\n\nProblem Statement: {}"""]

        # self.user_messages = [
        # """Give a BRIEF high-level procedure, in the form of a SHORT list of at most 5 steps, that lists the intermediate subgoals that should be performed using sympy, NOT YOU, to solve this problem. Do NOT try to solve the problem, do NOT include any computations or choices. Write [END PROCEDURE] when you have finished the list. An example is shown below.
        # Problem: For how many positive integers $m$ does the equation $||x-1|-2|=m/100$ have $4$ distinct solutions?""",
        # """Problem: {}
        # """
        #         ]
        # self.assistant_message_starts = [
        #     """[SHORT PROCEDURE]
        #     Procedure:
        #     1. Solve for the solution set of $||x-1|-2|=m/100$ where $m$ is a positive integer.
        #     2. Count the number of choices of $m$ where the solution set has 4 elements.
        #     [END PROCEDURE]""",
        #     """[SHORT PROCEDURE]
        #     Procedure:
        #     1."""
        # ]

    def get_prompt(self, history: list[dict[str, str]]) -> str:
        if history[-1]['role'] == 'user':
            main_message_added = False
            for msg in history:
                if msg['role'] == 'user' and msg['content'] == self.user_messages[0]:
                    main_message_added = True
                    break
            if not main_message_added:
                history_copy = copy.deepcopy(history)
                history.clear()
                # history.append({'role': 'user', 'content': self.user_messages[0]})
                # history.append({'role': 'assistant', 'content': self.assistant_message_starts[0]})
                history += history_copy  # This is to ensure that the user message is not lost
            history[-1]['content'] = self.user_messages[1].format(history[-1]['content'])
            # messages.append({'role': 'assistant', 'content': self.assistant_message_starts[1]})
            history.append({'role': 'assistant', 'content': "Sure I'll list the first couple steps.\n0. I would break down the problem into simpler steps, this can be done by the following\n1."})
        # return self.translate_for_deepseek(history, no_newline_after_assistant=True)
        return history

    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = OldPlannerPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"},
        # {"role": "assistant", "content": "The sum of 2 and 2 is 4"},
        # {"role": "user", "content": "What is the sum of 3 and 3?"},
        # {"role": "assistant", "content": "The sum of 3 and 3 is"}
    ]))
