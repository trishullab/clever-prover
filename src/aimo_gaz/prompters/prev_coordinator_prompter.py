from aimo_gaz.prompters.prompter import Prompter

class CoordinatorPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is a math problem statement.

Problem Statement: {}

You are the coordinator in charge of solving this problem. You have several tools at your disposal to help you solve it. Your tools are:

(1) planner: Query an LLM to generate the first few steps of a plan for solving the problem.
(2) coder: Query an LLM to generate code to solve the problem and then run the code. The most recently generated plan, if one exists, will be passed to the LLM coder.
(3) llm_guesser: Query an LLM to guess the answer to the problem.

If you think one of the previous tool outputs contains the correct answer, you also have the option to globally guess that answer. Simply output "[BEGIN GLOBAL GUESS]" before the numerical answer and "[END GLOBAL GUESS]" after it.

Here is the history of actions taken so far by the coordinator (you) and the tools to solve this problem:

[START HISTORY]
{}
[END HISTORY]

Please output which tool you would like to use next or, if you believe the problem has been solved, output your global guess for an answer.""" # TODO: add more [START] and [END] scaffolding

    def get_prompt(self, messages: list[dict[str, str]], history: list[str]) -> str:
        assert messages[-1]['role'] == 'user'
        messages[-1]['content'] = self.user_message.format(messages[-1]['content'], "\n".join(history))
        return messages

    def parse_response(self, response: str) -> str: # TODO: find a better way to do this and parse the guessed float within this method (maybe use enums with associated data)
        if "[BEGIN GLOBAL GUESS]" in response and "[END GLOBAL GUESS]" in response:
            # this does not include the '[END GLOBAL GUESS]'
            return response[response.rfind("[BEGIN GLOBAL GUESS]"):response.rfind("[END GLOBAL GUESS]")]
        
        tools = ["planner", "coder", "llm_guesser"]

        tool_rfinds = {}
        for tool in tools:
            tool_rfinds[tool] = response.rfind(tool)
        if max(tool_rfinds.values()) > -1:
            return max(tool_rfinds, key=tool_rfinds.get)
        
        ind_rfinds = {}
        for ind in range(len(tools)):
            ind_rfinds[tools[ind]] = response.rfind(str(ind+1))
        if max(ind_rfinds.values()) > -1:
            return max(ind_rfinds, key=ind_rfinds.get)
        
        return None


if __name__ == "__main__":
    prompter = CoordinatorPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
