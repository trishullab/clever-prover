The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation, and correctness definition.

Please write for me a detailed plan of the steps you would take to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec. Your plan should be formatted as described below.

If you believe that proving some helper lemmas first would be helpful to proving correctness, start your plan by describing these lemmas. (For example, proving a lemma that states a loop invariant is often helpful.) For each lemma, output the keyword `[LEMMA PLAN]` followed by a natural language description of the lemma and a plan for proving it. Then, output the keyword `[LEMMA]` followed by the lemma statement in Lean 4. Fill in the proof of the lemma with `sorry`; do NOT write the tactics to prove the lemma. End the lemma statement with the keyword `[END]`.

Be sure to only output the lemmas that are necessary to prove the correctness definition. Do not output extraneous lemmas.

After (optionally) describing the lemmas, output the keyword `[CORRECTNESS PLAN]` followed by a detailed natural language plan of the steps you would take to prove the correctness definition. You may freely use any of your lemmas in this correctness proof. End the correctness plan with the keyword `[END]`.

--------------------------------------------------

[PROBLEM STATEMENT]
/--
function_signature: "def truncate_number(number: float) -> float"
docstring: |
    Given a positive floating point number, it can be decomposed into
    and integer part (largest integer smaller than given number) and decimals
    (leftover part always smaller than 1).
test_cases:
  - input: 3.5
    expected_output: 0.5
--/
[END]

[PROBLEM SPEC]
def problem_spec
-- function signature
(impl: Rat → Rat)
-- inputs
(number: Rat) :=
-- spec
let spec (res):=
0 ≤ res ∧ res < 1 ∧
number = number.floor + res;
-- program terminates
∃ result, impl number = result →
-- return value satisfies spec
spec result
[END]

[FUNCTION IMPLEMENTATION]

[END]

[CORRECTNESS DEFINITION]
theorem correctness
(number: Rat)
: problem_spec implementation number := by
sorry
[END]