from aimo_gaz.prompts.prompt import ConcatPrompt

class CoordinatorPrompt(ConcatPrompt):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt: str = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt,
                         append_system_prompt_after_every_message)
        self.system_prompt = None
        self.user_message = """Below is a math problem statement.

Problem Statement: {}

You are the coordinator in charge of solving this problem. You have several tools at your disposal to help you solve it. Your tools are:

(1) llm_guesser: Query an LLM to guess the answer to the problem.

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
            return response[response.find("[BEGIN GLOBAL GUESS]"):response.find("[END GLOBAL GUESS]")]
        if "llm_guesser" in response:
            return "llm_guesser"
        if "1" in response:
            return "llm_guesser"
        return None


if __name__ == "__main__":
    prompter = CoordinatorPrompt()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
