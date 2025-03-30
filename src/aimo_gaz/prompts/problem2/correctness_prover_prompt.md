The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, a function implementation, a list of zero or more previously-proven lemmas about the function implementation (with their proofs omitted), and a correctness definition.

Along with these is a detailed plan with steps of how to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec.

Please write for me a Lean 4 proof of the correctness definition, starting with the correctness theorem statement. You may freely use any of the lemmas in your proof.

Please respond entirely in Lean 4.

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

[LEMMAS]

[END]

[CORRECTNESS DEFINITION]
theorem correctness
(number: Rat)
: problem_spec implementation number := by
sorry
[END]

[PLAN]

[END]