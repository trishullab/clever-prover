The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, a function implementation, a list of zero or more previously-proven lemmas about the function implementation (with their proofs omitted), and a correctness definition.

Along with these is a detailed plan with steps of how to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec.

Please write for me a Lean 4 proof of the correctness definition, starting with the correctness theorem statement. You may freely use any of the lemmas in your proof.

Please respond entirely in Lean 4.

--------------------------------------------------

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

[FUNCTION IMPLEMENTATION]

[END]

[LEMMAS]

[END]

[CORRECTNESS DEFINITION]
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
sorry
[END]

[PLAN]

[END]