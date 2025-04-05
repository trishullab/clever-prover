```lean
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
  -- Unfold the definition of problem_spec
  unfold problem_spec
  
  -- Let result be the output of our implementation
  let result := implementation operations
  exists result
  
  -- Assume implementation returns result
  intro h_impl
  
  -- Use our lemma to connect implementation result to below_zero_condition
  have h_equiv := process_below_zero_equiv operations 0
  unfold implementation at h_impl
  
  -- Case analysis on the result
  cases h : result
  
  -- Case: result = false
  case false =>
    -- Need to prove: ¬below_zero_condition
    rw [h] at h_impl
    unfold below_zero_condition
    
    -- Apply the lemma (contrapositive)
    rw [←h_equiv]
    exact h_impl
    
  -- Case: result = true
  case true =>
    -- Need to prove: below_zero_condition
    rw [h] at h_impl
    unfold below_zero_condition
    
    -- Apply the lemma directly
    rw [←h_equiv]
    exact h_impl
```