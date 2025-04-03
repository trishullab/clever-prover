```lean
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
  -- Unfold the problem specification
  unfold problem_spec
  
  -- Let result be the output of the implementation
  let result := implementation operations
  
  -- Show there exists a result such that if impl operations = result, then spec result
  use result
  
  -- Prove: impl operations = result → spec result
  intro h_impl
  
  -- Define what spec result means
  unfold spec
  
  -- Use our lemma that characterizes the implementation
  have h_characterization : implementation operations = true ↔ 
    ∃ i, i ≤ operations.length ∧ (operations.take i).sum < 0 := 
    implementation_characterization operations
  
  -- Case analysis on whether result is true or false
  by_cases h_result : result
  
  -- Case: result = true
  · -- Need to show below_zero_condition holds
    simp [h_result]
    -- Use the impl_equals_result hypothesis to rewrite
    rw [← h_impl] at h_characterization
    -- Since result is true, we know implementation operations = true
    simp [h_result] at h_characterization
    -- Therefore below_zero_condition holds
    exact h_characterization
  
  -- Case: result = false
  · -- Need to show ¬below_zero_condition holds
    simp [h_result]
    -- Use the impl_equals_result hypothesis to rewrite
    rw [← h_impl] at h_characterization
    -- Since result is false, we know implementation operations = false
    simp [h_result] at h_characterization
    -- By contraposition, ¬below_zero_condition holds
    push_neg at h_characterization
    exact h_characterization
```