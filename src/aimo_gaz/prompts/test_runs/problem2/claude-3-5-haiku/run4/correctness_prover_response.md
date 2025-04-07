Here's a Lean 4 proof for the truncate_number problem:

```lean
theorem correctness
(number: Rat)
: problem_spec implementation number := by
  unfold problem_spec
  -- Use implementation directly
  let result := implementation number
  use result
  simp [implementation]
  
  -- Break the spec into three parts
  apply And.intro
  
  -- Part 1: Result is non-negative
  · have h_floor_le_number : number.floor ≤ number := by 
      exact Rat.floor_le number
    calc 
      0 ≤ number - number.floor := by 
        apply sub_nonneg.mpr h_floor_le_number
  
  -- Part 2: Result is less than 1
  · have h_sub_lt_one : number - number.floor < 1 := by
      exact Rat.sub_floor_lt number
  
  -- Part 3: Reconstruction property
  · have h_reconstruction : number = number.floor + (number - number.floor) := by
      rw [← Rat.sub_add_cancel number number.floor]
    exact h_reconstruction
```

The proof follows the plan by:
1. Directly implementing the `implementation` function as calculating `number - number.floor`
2. Breaking the specification into three parts
3. Using built-in Rat lemmas to prove each part:
   - `Rat.floor_le` shows the floor is always less than or equal to the number
   - `Rat.sub_floor_lt` shows the subtraction will always be less than 1
   - Simple algebra shows we can reconstruct the original number by adding floor and remainder

The proof leverages Lean 4's rational number properties to succinctly demonstrate the truncation function's correctness.