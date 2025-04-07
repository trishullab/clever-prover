The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation, and correctness definition.

Please write for me a detailed plan of the steps you would take to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec. Your plan should be formatted as described below.

If you believe that proving some helper lemmas first would be helpful to proving correctness, start your plan by describing these lemmas. (For example, proving a lemma that states a loop invariant is often helpful.) For each lemma, output the keyword `[LEMMA PLAN]` followed by a natural language description of the lemma and a plan for proving it. Then, output the keyword `[LEMMA]` followed by the lemma statement in Lean 4. Fill in the proof of the lemma with `sorry`; do NOT write the tactics to prove the lemma. End the lemma statement with the keyword `[END]`.

Be sure to only output the lemmas that are necessary to prove the correctness definition. Do not output extraneous lemmas.

After (optionally) describing the lemmas, output the keyword `[CORRECTNESS PLAN]` followed by a detailed natural language plan of the steps you would take to prove the correctness definition. You may freely use any of your lemmas in this correctness proof. End the correctness plan with the keyword `[END]`.

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

[CORRECTNESS DEFINITION]
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
sorry
[END]