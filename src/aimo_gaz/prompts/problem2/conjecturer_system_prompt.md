The instructions below describe a coding problem statement with a corresponding Lean 4 problem spec, function implementation, and correctness definition.

Along with these is a detailed plan with steps of how to prove the correctness definition in Lean 4 stating that the given function implementation follows the required problem spec.

Please write for me a list of conjectured lemmas in Lean 4 that will be useful for carrying out this proof. Fill in the proofs of these lemmas with `sorry`; do NOT write the tactics to prove these lemmas.

Please respond entirely in Lean 4.

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
def implementation (number: Rat) : Rat :=
number - number.floor
[END]

[CORRECTNESS DEFINITION]
theorem correctness
(number: Rat)
: problem_spec implementation number := by
sorry
[END]

[PLAN]
To prove that the given function implementation satisfies the problem specification in Lean 4, we will follow these detailed steps:

1. **Understand the Problem Specification**: 
   - The problem specifies that we need to demonstrate that the implementation `number - number.floor` results in a value (`result`) such that it meets the specification of being the decimal part of the input `number`.

2. **Analyze the Function Implementation**:
   - The implementation calculates `number - number.floor`, which effectively subtracts the largest integer less than or equal to `number` from `number` itself. This subtraction leaves us with the decimal part of the number, as intended. 

3. **Define the Specification**:
   - The specification (`spec`) is defined as `res = number - number.floor`. This means that for any `res` that results from our implementation, `res` must equal the decimal remainder of `number`.

4. **Establish the Theorem**:
   - Our goal is to affirm that `problem_spec implementation number` is correct. This can be broken down as follows:
      - Show that the implementation produces a result.
      - Demonstrate that the result satisfies the specification outlined.

5. **Formalize the Proof Outline**:
   - We will use the theorem `correctness`, which states that for any positive rational number `number`, the implementation meets the specification.

6. **Constructing the Proof**:
   - **Step 1**: Assume an arbitrary positive rational `number`.
   - **Step 2**: Evaluate the implementation `implementation number`, which gives us `number - number.floor`.
   - **Step 3**: Let `result := implementation number`, implying `result = number - number.floor`.
   - **Step 4**: Show that `result` satisfies the specification.
     - We need to show that `result` fulfills the condition `spec result`, which is effectively `result = number - number.floor`.
     - Given how we defined `result`, this holds directly.

7. **Use Lean's Tactics**:
   - Implement the proof in Lean using appropriate tactics:
     - `have` to state intermediate results.
     - `exact` to unify the left and right sides of the equation.
     - Utilize `exists` to express the existence of some `result`.

8. **Conclude the Proof**:
   - Confirm all the steps lead back to the requirement of the specification, encapsulating our entire argument in the framework of Lean.

9. **Wrap Up with a Comment**:
   - Add a comment at the end of the theorem to clarify that the proof establishes that our implementation properly extracts the decimal part of a given positive floating point number as intended.

Now that we have established these steps, we can proceed to formalize the proof in Lean 4 using the provided framework. Each step will be carefully articulated within the Lean environment to validate the correctness of our implementation against the specifications required.
[END]