from clever_prover.prompters.prompter import Prompter

class ImplementationPlannerPrompter(Prompter):
    def __init__(self, system_prompt_path: str = None, example_prompt_path: str = None, system_prompt: str = None,
                 example_prompt_list: list[dict[str, str]] = None, append_system_prompt_after_every_message: bool = False):
        super().__init__(system_prompt_path, example_prompt_path, system_prompt, example_prompt_list,
                         append_system_prompt_after_every_message)
        assert self.system_prompt is not None
        assert self.example_prompt_list

        self.user_prompt = """[PROBLEM STATEMENT]
{}
[END]

[PROBLEM SPEC]
{}
[END]

[FUNCTION IMPLEMENTATION SIGNATURE]
{}
[END]

[TEST CASES]
{}
[END]"""

        self.stop_tokens = []

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, implementation_signature: str, test_cases: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history[1:1] = self.example_prompt_list
        history.append({"role": "user", "content": self.user_prompt.format(problem_statement, problem_spec, implementation_signature, test_cases)})
        return history

    def parse_response(self, response: str) -> str:
        return response.strip()


if __name__ == "__main__":
    prompter = ImplementationPlannerPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
