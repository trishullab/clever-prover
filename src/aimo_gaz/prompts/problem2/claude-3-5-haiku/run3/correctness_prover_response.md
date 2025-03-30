I'll provide a Lean 4 proof for the correctness theorem based on the provided implementation and specification:

```lean
theorem correctness
(number: Rat)
: problem_spec implementation number := by
  -- Unfold the problem specification
  unfold problem_spec

  -- Set the result to the implementation 
  let result := implementation number

  -- Prove three parts of the specification 
  constructor
  · -- Part 1: 0 ≤ result 
    unfold implementation
    apply sub_nonneg.mpr
    apply le_floor

  constructor  
  · -- Part 2: result < 1
    unfold implementation
    apply floor_lt

  · -- Part 3: number = number.floor + result
    unfold implementation
    rfl

  -- Prove implementation terminates
  use result
  rfl
```

This proof follows the strategy outlined in the plan:

1. Uses `constructor` to break down the `problem_spec` into its component parts
2. First proves the result is non-negative by applying `sub_nonneg.mpr` and `le_floor`
3. Then proves the result is less than 1 by applying `floor_lt`
4. Uses reflexivity (`rfl`) to prove the reconstruction property
5. Proves termination by using `use result` and `rfl`

The key steps leverage built-in Lean properties of rational numbers, particularly around the `floor` function. The implementation is simple subtraction of the floor from the original number, which naturally satisfies the specification.

The proof assumes standard Lean lemmas about rational numbers and floor operations are available in the context.