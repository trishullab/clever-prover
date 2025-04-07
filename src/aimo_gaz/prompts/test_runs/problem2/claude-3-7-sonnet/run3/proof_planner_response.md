# Proof Plan for Truncate Number Correctness

To prove that the `implementation` function correctly follows the `problem_spec` for truncating a rational number, I'll outline a detailed plan for the Lean 4 proof.

## Step 1: Unfold the definitions and set up the proof

First, I'll unfold the definitions of `problem_spec` and `implementation` to clarify what needs to be proven:
- Establish that the implementation returns `number - number.floor`
- Set up the goal to show this result satisfies the three required properties

## Step 2: Prove the result is non-negative (0 ≤ res)

To prove the first condition:
- Use a fundamental property of the floor function: `number.floor ≤ number` for any rational number
- From this, show that `number - number.floor ≥ 0`
- This requires using Lean's library properties of floor and arithmetic inequality manipulation

## Step 3: Prove the result is less than 1 (res < 1)

For the second condition:
- Use another fundamental property of the floor function: `number < number.floor + 1`
- From this property, derive that `number - number.floor < 1`
- This will require some basic algebraic manipulation in Lean

## Step 4: Prove the decomposition property (number = number.floor + res)

For the third condition:
- Start with `res = number - number.floor` (from the implementation)
- Algebraically rearrange to show `number.floor + res = number.floor + (number - number.floor) = number`
- This is a straightforward algebraic identity that should be easily provable in Lean

## Step 5: Combine the proofs to satisfy the existential

Finally:
- Instantiate the existential quantifier with `result := number - number.floor`
- Show that this value satisfies all three conditions using the sub-proofs from steps 2-4
- Apply the necessary tactics to complete the proof

This proof should be relatively straightforward as it relies primarily on basic properties of the floor function and elementary algebraic manipulation. The main challenge will be correctly using Lean's library properties of rational numbers and the floor function.