from aimo_gaz.prompters.prompter import Prompter

class PlannerPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        assert self.system_prompt is not None # TODO: add examples # TODO: include custom system prompt for proving?
        self.default_user_instructions = "Please write the steps now."
        
        self.stop_tokens = []

    def get_prompt(self, history: list[dict[str, str]], tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
        instructions = tool_prompt if tool_prompt else self.default_user_instructions
        history.append({"role": "user", "content": f"[INSTRUCTIONS]\n{instructions}\n[END]"})
        return history

    def parse_response(self, response: str) -> str:
        return response.strip()


if __name__ == "__main__":
    prompter = PlannerPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
