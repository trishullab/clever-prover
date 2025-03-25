The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation signature, and test cases.

Please write for me a detailed plan of the steps you would take to implement a Lean 4 function to solve this problem.

Please respond mostly in natural language.

[PROBLEM STATEMENT]
/--
function_signature: "def below_zero(operations: List[int]) -> bool"
docstring: |
    You're given a list of deposit and withdrawal operations on a bank account that starts with
    zero balance. Your task is to detect if at any point the balance of account fallls below zero, and
    at that point function should return True. Otherwise it should return False.
test_cases:
  - input:
      - 1
      - 2
      - 3
    expected_output: false
  - input:
      - 1
      - 2
      - -4
      - 5
    expected_output: true
-/
[END]

[PROBLEM SPEC]
def problem_spec
-- function signature
(impl: List Int → Bool)
-- inputs
(operations: List Int) :=
-- spec
let below_zero_condition := ∃ i, i ≤ operations.length ∧
(operations.take i).sum < 0;
let spec (result: Bool) :=
if result then below_zero_condition else ¬below_zero_condition;
-- program terminates
∃ result, impl operations = result →
-- return value satisfies spec
spec result
[END]

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (operations: List Int) : Bool :=
sorry
[END]

[TEST CASES]
#test implementation [1, 2, 3] = false
#test implementation [1, 2, -4, 5] = true
[END]