import typing
from clever_prover.prompters.prompter import Prompter

class ProofPlannerPrompter(Prompter):
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

[FUNCTION IMPLEMENTATION]
{}
[END]

[CORRECTNESS DEFINITION]
{}
[END]"""

        self.stop_tokens = []

    def get_prompt(self, history: list[dict[str, str]], problem_statement: str, problem_spec: str, implementation: str, correctness_definition: str) -> list[dict[str, str]]:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": self.system_prompt})
            history[1:1] = self.example_prompt_list
        history.append({"role": "user", "content": self.user_prompt.format(problem_statement, problem_spec, implementation, correctness_definition)})
        return history

    def parse_response(self, response: str) -> typing.Tuple[str, list[str], list[str], str]:
        raw_response = response.strip()

        lemmas = []
        lemma_plans = []
        lemma_plan_start_ind = response.find("[LEMMA PLAN]")
        while lemma_plan_start_ind != -1:
            response = response[(lemma_plan_start_ind + len("[LEMMA PLAN]")):]
            lemma_start_ind = response.find("[LEMMA]")
            lemma_end_ind = response.find("[END]")
            if lemma_start_ind != -1 and lemma_end_ind != -1 and lemma_start_ind < lemma_end_ind:
                lemma_plans.append(response[:lemma_start_ind].strip())
                lemmas.append(response[(lemma_start_ind + len("[LEMMA]")):lemma_end_ind].strip())
                response = response[(lemma_end_ind + len("[END]")):]

            lemma_plan_start_ind = response.find("[LEMMA PLAN]")
        
        correctness_plan = "N/A"
        correctness_plan_start_ind = response.find("[CORRECTNESS PLAN]")
        if correctness_plan_start_ind != -1:
            correctness_plan_response = response[(correctness_plan_start_ind + len("[CORRECTNESS PLAN]")):]
            correctness_plan_end_ind = correctness_plan_response.find("[END]")
            if correctness_plan_end_ind != -1:
                correctness_plan = correctness_plan_response[:correctness_plan_end_ind].strip()
            else:
                correctness_plan = correctness_plan_response.strip()

        return raw_response, lemmas, lemma_plans, correctness_plan


if __name__ == "__main__":
    prompter = ProofPlannerPrompter()
    print(prompter.get_prompt([
        {"role": "user", "content": "What is the sum of 2 and 2?"}
    ]))
