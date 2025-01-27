import typing
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.solver.tools.coordinator_tool import ToolOrGlobalGuess
from aimo_gaz.scripts.eval import ProblemType

class CoordinatorPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = """Below is a math problem statement.

You are the coordinator in charge of {} this problem. You have several tools at your disposal to help you solve it. Your tools are:

(1) planner: Query an LLM to generate the first few steps of a plan for solving the problem. You can use this plan later in custom instructions for other tools.
(2) coder: Query an LLM to generate code to help solve the problem and then run the code.
(3) llm_guesser: Query an LLM to guess an answer to help solve the problem.
(4) prover: Query an LLM to guess the next tactic for proving the problem in Lean 4. The LLM will be provided the current proof state. You can later choose this tactic as input to the lean4_executor. You should only use this tool if you are formally proving the problem.
(5) lean4_executor: Input a Lean 4 tactic to execute the next step to formally prove the problem in Lean 4. Please output the tactic between the tokens '[START TACTIC]' and '[END TACTIC]'. You should only use this tool if you are formally proving the problem.

If you think one of the previous tool outputs contains the correct answer, you also have the option to globally guess that answer. Do not do this if you are formally proving the problem.

Please output which tool you would like to use next or, if you are not formally proving the problem and believe the problem has been solved, output your global guess for an answer.

If you choose to use a tool, please output the name of the tool between the tokens '[START TOOL]' and '[END TOOL]'
Then for LLM tools, output custom instructions for the tool to follow between the tokens '[START PROMPT]' and '[END PROMPT]'. These instructions can use previously generated plans.

If you choose to globally guess the answer, please output your numerical answer between the tokens '[START GLOBAL GUESS]' and '[END GLOBAL GUESS]'. Only include the guessed number, as an integer or a fraction.

Below is the problem statement and the history of actions taken so far by the coordinator (you) and the tools to solve this problem.""" # TODO: add examples
        self.system_prompt_format_find = "solving"
        self.system_prompt_format_prove = "formally proving"
        self.problem_statement_message = "Problem Statement: {}"
        self.user_message = "Please output your chosen tool and prompt or your global guess now."

        self.stop_tokens = ["[END PROMPT]", "[END TACTIC]", "[END GLOBAL GUESS]"]

        self.saved_problem_type = None

    def get_prompt(self, history: list[dict[str, str]], problem_description: str, problem_type: ProblemType) -> list[dict[str, str]]:
        if self.saved_problem_type is None:
            self.saved_problem_type = problem_type
        if self.saved_problem_type != problem_type:
            history.clear() # TODO: maybe preserve history across problem_type change in the future
            self.saved_problem_type = problem_type
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt.format(self.system_prompt_format_find if problem_type == ProblemType.FIND else self.system_prompt_format_prove)})
            history.insert(1, {"role": "user", "content": self.problem_statement_message.format(problem_description)})
        history.append({"role": "user", "content": self.user_message})
        return history

    def parse_response(self, response: str) -> typing.Tuple[ToolOrGlobalGuess, str, str]:
        actual_tool_ind = response.find("[START TOOL]")
        if actual_tool_ind != -1:
            tool_response = response[actual_tool_ind + len("[START TOOL]"):]
            actual_tool_ind = tool_response.find("[END TOOL]")
            if actual_tool_ind != -1:
                tool_response = tool_response[:actual_tool_ind]
            tool_response = tool_response.strip()
            tool = None
            for iter_tool in ToolOrGlobalGuess:
                if tool_response == iter_tool.value:
                    tool = iter_tool
            if not tool:
                return None, None, None
            
            tool_prompt = None
            start_prompt_token = "[START TACTIC]" if tool == ToolOrGlobalGuess.LEAN4_EXECUTOR else "[START PROMPT]"
            actual_tool_prompt_ind = response.rfind(start_prompt_token)
            if actual_tool_prompt_ind != -1:
                tool_prompt_response = response[actual_tool_prompt_ind + len(start_prompt_token):]
                tool_prompt = tool_prompt_response.strip()
            
            return tool, tool_prompt, None

        actual_guess_ind = response.rfind("[START GLOBAL GUESS]")
        if actual_guess_ind != -1:
            response = response[actual_guess_ind + len("[START GLOBAL GUESS]"):]
            return ToolOrGlobalGuess.GLOBAL_GUESS, None, response.strip()
        
        return None, None, None


if __name__ == "__main__":
    prompter = CoordinatorPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
