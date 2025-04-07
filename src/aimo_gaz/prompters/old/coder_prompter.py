from aimo_gaz.prompters.prompter import Prompter

class CoderPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        assert self.system_prompt is not None # TODO: add examples
        self.default_user_instructions = "Please write the code now."
        
        self.stop_tokens = ["[END]"]

    def get_prompt(self, history: list[dict[str, str]], tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
        instructions = tool_prompt if tool_prompt else self.default_user_instructions
        history.append({"role": "user", "content": f"[INSTRUCTIONS]\n{instructions}\n[END]"})
        return history

    def parse_response(self, response: str) -> str:
        actual_code_ind = response.find("[CODE]")
        if actual_code_ind != -1:
            response = response[(actual_code_ind + len("[CODE]")):]
        return response.strip()
