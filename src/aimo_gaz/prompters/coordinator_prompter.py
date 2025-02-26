import typing
from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.solver.tools.coordinator_tool import ToolOrOther
from aimo_gaz.scripts.eval import ProblemState
from aimo_gaz.utils import string_utils

class CoordinatorPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        assert self.system_prompt is not None # TODO: add examples
        self.user_instructions_find = """This problem requires an answer to be inserted. Please choose tools that will help you find the answer.

Please output your chosen tool and prompt or your global guess now."""
        self.user_instructions_prove = """This problem does not require an answer to be inserted. Please choose tools that will help you formally prove the problem.

Please output your chosen tool and prompt/tactic now."""
        self.user_instructions_prove_after_find = """Your guess for the answer to this problem has been inserted. Please choose tools that will help you formally prove the problem.

Please output your chosen tool and prompt/tactic now."""

        self.stop_tokens = ["[END PROMPT]", "[END TACTIC]", "[END GLOBAL GUESS]"]

    def get_prompt(self, history: list[dict[str, str]], history_buffer: list[str], problem_statement: str, theorem_statement: str, problem_state: ProblemState) -> list[dict[str, str]]:
        user_message = ""
        
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            user_message += string_utils.format_problem_statements(problem_statement, theorem_statement) + "\n\n"
        
        if history_buffer:
            user_message += "[MESSAGE]\n" + "\n\n[MESSAGE]\n".join(history_buffer) + "\n\n"

        if problem_state == ProblemState.FINDING:
            user_instructions = self.user_instructions_find
        elif problem_state == ProblemState.PROVING:
            user_instructions = self.user_instructions_prove
        else:
            user_instructions = self.user_instructions_prove_after_find
        user_message += "[INSTRUCTIONS]\n" + user_instructions

        history.append({"role": "user", "content": user_message})

        return history

    def parse_response(self, response: str) -> typing.Tuple[ToolOrOther, str, str]:
        # this silently fixes a common error # TODO: maybe delete this special case after adjusting rewrite command?
        has_tactic = False
        if response.find("[START TACTIC]") != -1:
            has_tactic = True
            tool = ToolOrOther.LEAN4_EXECUTOR
        
        actual_tool_ind = response.find("[START TOOL]")
        if actual_tool_ind != -1 or has_tactic:
            if not has_tactic:
                tool_response = response[actual_tool_ind + len("[START TOOL]"):]
                actual_tool_ind = tool_response.find("[END TOOL]")
                if actual_tool_ind != -1:
                    tool_response = tool_response[:actual_tool_ind]
                tool_response = tool_response.strip()
                tool = None
                for iter_tool in ToolOrOther:
                    if tool_response == iter_tool.value:
                        tool = iter_tool
                        break
                if not tool:
                    return None, None, None
            
            tool_prompt = None
            start_prompt_token = "[START TACTIC]" if tool == ToolOrOther.LEAN4_EXECUTOR else "[START PROMPT]"
            actual_tool_prompt_ind = response.rfind(start_prompt_token)
            # this silently fixes a common error
            if actual_tool_prompt_ind == -1 and tool == ToolOrOther.LEAN4_EXECUTOR:
                start_prompt_token = "[START PROMPT]"
                actual_tool_prompt_ind = response.rfind(start_prompt_token)
            if actual_tool_prompt_ind != -1:
                tool_prompt_response = response[actual_tool_prompt_ind + len(start_prompt_token):]
                tool_prompt = tool_prompt_response.strip()
            
            return tool, tool_prompt, None

        actual_global_guess_ind = response.rfind("[START GLOBAL GUESS]")
        if actual_global_guess_ind != -1:
            response = response[actual_global_guess_ind + len("[START GLOBAL GUESS]"):]
            return ToolOrOther.GLOBAL_GUESS, None, response.strip()
        
        actual_re_guess_ind = response.rfind("[RE-GUESS]")
        if actual_re_guess_ind != -1:
            return ToolOrOther.RE_GUESS, None, None
        
        return None, None, None


if __name__ == "__main__":
    prompter = CoordinatorPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
