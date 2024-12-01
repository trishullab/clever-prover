from aimo_gaz.prompters.prompter import Prompter

class PlannerPrompter(Prompter):

    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

Write for me the first couple steps you would do to solve this problem. Only write the first couple steps please.

Please start your response with: '0. I would break down the problem into simpler steps, this can be done by the following:'
Please end your response with: '[END PROCEDURE]'""" # TODO: add examples
        self.problem_statement_message = "Problem Statement: {}" # TODO: have coordinator pass in input instead of hardcoding it; do this for all tools
        self.user_message = "Please write the steps now."
        
        self.stop_tokens = ["[END PROCEDURE]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": self.user_message})
        return history

    def parse_response(self, response: str) -> str:
        return response


if __name__ == "__main__":
    prompter = PlannerPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
