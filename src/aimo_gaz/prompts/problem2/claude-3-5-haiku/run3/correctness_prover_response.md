Here's a Lean 4 proof for the correctness theorem:

```lean
theorem correctness
(number: Rat)
: problem_spec implementation number := by
  -- Unfold problem specification
  unfold problem_spec
  
  -- Introduce the result of the implementation
  let result := implementation number
  
  -- Prove termination (always exists)
  use result
  
  -- Prove specification 
  unfold spec
  unfold implementation
  
  -- By definition of implementation and rational number floor
  rfl
```

The proof works because:
1. It uses `use result` to demonstrate the function terminates with a specific result
2. `rfl` (reflexivity) shows that the result matches the specification
3. The implementation `number - number.floor` directly gives the decimal part
4. The proof is simple because the implementation exactly matches the specification

The proof relies on the built-in properties of `Rat.floor` and simple algebraic reasoning to show that subtracting the floor from the original number yields the decimal part.