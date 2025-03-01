from aimo_gaz.prompters.prompter import Prompter
from aimo_gaz.utils import string_utils

class ProverPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        assert self.system_prompt is not None
        assert self.example_prompt_list
        self.default_user_instructions = "Please write the next tactic now."
        
        self.stop_tokens = ["[END TACTIC]"]

    def get_prompt(self, history: list[dict[str, str]], proof_state_render: str, tool_prompt: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history[1:1] = self.example_prompt_list
        instructions = tool_prompt if tool_prompt else self.default_user_instructions
        history.append({"role": "user", "content": f"{proof_state_render}\n\n[INSTRUCTIONS]\n{instructions}"})
        return history

    def parse_response(self, response: str) -> str:
        actual_tactic_ind = response.rfind("[START TACTIC]")
        if actual_tactic_ind != -1:
            response = response[(actual_tactic_ind + len("[START TACTIC]")):]
        return response.strip()
