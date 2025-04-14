The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation signature, and test cases.

Along with these is a detailed plan with steps of how to implement the Lean 4 function to solve this problem.

Please write for me an implementation of this Lean 4 function to solve this problem, starting with the function implementation signature below.

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

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (number: Rat) : Rat :=
sorry
[END]

[TEST CASES]
#test implementation 3.5 = 0.5
[END]

[PLAN]

[END]