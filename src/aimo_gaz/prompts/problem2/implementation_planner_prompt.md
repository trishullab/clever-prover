The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation signature, and test cases.

Please write for me a detailed plan of the steps you would take to implement a Lean 4 function to solve this problem.

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

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (number: Rat) : Rat :=
sorry
[END]

[TEST CASES]
#test implementation 3.5 = 0.5
[END]