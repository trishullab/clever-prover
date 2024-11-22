import typing
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.solver.tools.coordinator_tool import ToolOrGlobalGuess
from aimo_gaz.utils import string_utils

class CoordinatorPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

You are the coordinator in charge of solving this problem. You have several tools at your disposal to help you solve it. Your tools are:

(1) planner: Query an LLM to generate the first few steps of a plan for solving the problem.
(2) coder: Query an LLM to generate code to solve the problem and then run the code. The most recently generated plan, if one exists, will be passed to the LLM coder.
(3) llm_guesser: Query an LLM to guess the answer to the problem. The most recently generated plan, if one exists, will be passed to the LLM guesser.

If you think one of the previous tool outputs contains the correct answer, you also have the option to globally guess that answer.

Please output which tool you would like to use next or, if you believe the problem has been solved, output your global guess for an answer.

If you choose to use a tool, please output the name of the tool between the tokens '[START TOOL]' and '[END TOOL]'
If you choose to globally guess the answer, please output your numerical answer between the tokens '[START GLOBAL GUESS]' and '[END GLOBAL GUESS]'. Only include the guessed number, as an integer or a fraction.

Below is the problem statement and the history of actions taken so far by the coordinator (you) and the tools to solve this problem.""" # TODO: add examples
        self.problem_statement_message = "Problem Statement: {}"
        self.user_message = "Please output your chosen tool or global guess now."

        self.stop_tokens = ["[END TOOL]", "[END GLOBAL GUESS]"]

    def get_prompt(self, history: list[dict[str, str]], problem_description: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": self.user_message})
        return history

    def parse_response(self, response: str) -> typing.Tuple[ToolOrGlobalGuess, str, float]:
        actual_tool_ind = response.rfind("[START TOOL]")
        if actual_tool_ind != -1:
            response = response[actual_tool_ind + len("[START TOOL]"):]
            response = response.strip()
            for tool in ToolOrGlobalGuess:
                if response == tool.value:
                    return tool, None, None
            return None, None, None

        actual_guess_ind = response.rfind("[START GLOBAL GUESS]")
        if actual_guess_ind != -1:
            response = response[actual_guess_ind + len("[START GLOBAL GUESS]"):]
            response = response.strip()
            return ToolOrGlobalGuess.GLOBAL_GUESS, response, string_utils.parse_float(response)
        
        return None, None, None


if __name__ == "__main__":
    prompter = CoordinatorPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
