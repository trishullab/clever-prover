The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation, and correctness definition.

Please write for me a detailed plan of the steps you would take to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec.

Please respond mostly in natural language.

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
res = number - number.floor;
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