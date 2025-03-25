The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation, and correctness definition.

Along with these is a detailed plan with steps of how to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec.

Please write for me a list of conjectured lemmas in Lean 4 that will be useful for carrying out this proof. Fill in the proofs of these lemmas with `sorry`; do NOT write the tactics to prove these lemmas.

Please respond entirely in Lean 4.

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
def implementation (operations: List Int) : Bool :=
let rec check (ops : List Int) (acc : Int) : Bool :=
  match ops with
  | []        => false
  | op :: ops' =>
    let new_acc := acc + op
    if new_acc < 0 then true else check ops' new_acc
check operations 0
[END]

[CORRECTNESS DEFINITION]
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
sorry
[END]

[PLAN]
I'll outline a detailed plan for proving the correctness of the `below_zero` function in Lean 4. Here's a step-by-step approach:

1. Understand the Problem and Spec
- The function checks if a running balance ever goes below zero during a sequence of deposit/withdrawal operations
- The spec requires returning true if there's a point where the running sum becomes negative
- The implementation uses a recursive helper function that tracks the running balance

2. Proof Strategy
The proof will likely involve:
a) Showing the function always terminates
b) Proving the implementation matches the specification
c) Using structural induction on the input list

3. Key Proof Techniques
- Induction on the list of operations
- Case analysis on the first operation
- Tracking running balance and its properties
- Dealing with the recursive structure of the implementation

4. Detailed Proof Plan
- Start by introducing the input list of operations
- Perform induction on the list structure
- Base case (empty list):
  * Show balance remains zero
  * Prove no negative point exists
- Inductive step:
  * Consider first operation and its impact on balance
  * Recursively analyze remaining operations
  * Prove either:
    - Balance never goes negative
    - First point of negative balance is found

5. Proof Skeleton Outline
- Use structural induction
- Handle base case of empty list
- For non-empty list, consider two scenarios:
  1. First operation doesn't cause negative balance
  2. First operation causes negative balance
- Use recursion and induction hypothesis to prove correctness

6. Lean 4 Proof Tactics to Use
- `induction` for list structural induction
- `simp` for simplifying expressions
- `have` for introducing intermediate assertions
- `apply` for applying existing lemmas
- `cases` for case analysis

7. Potential Challenges
- Proving the existential condition in the specification
- Showing equivalence between recursive implementation and spec
- Handling different list lengths and operation sequences

Would you like me to elaborate on any specific part of this proof strategy?
[END]