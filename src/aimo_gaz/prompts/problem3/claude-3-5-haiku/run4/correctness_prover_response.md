Here's a Lean 4 proof for the correctness theorem:

```lean
theorem correctness
(operations: List Int)
: problem_spec implementation operations
:= by
  unfold problem_spec
  have h_result := implementation operations
  use h_result
  simp [implementation]
  
  -- Break into two cases: True and False
  by_cases h_result_true : h_result = true
  
  -- Case 1: Result is True
  · have h_exists_negative_prefix := true_implies_negative_balance operations h_result_true
    unfold problem_spec.spec
    simp [h_result_true]
    obtain ⟨i, h_i_positive, h_i_len, h_sum_negative⟩ := h_exists_negative_prefix
    exact ⟨i, h_i_len, h_sum_negative⟩

  -- Case 2: Result is False  
  · have h_no_negative_prefix := false_implies_no_negative_balance operations (by simp [h_result_true])
    unfold problem_spec.spec
    simp [h_result_true]
    intro i h_i_conditions h_sum_lt_zero
    have h_contradiction := h_no_negative_prefix i h_i_conditions
    contradiction
```

This proof follows the plan outlined earlier:
1. It uses `true_implies_negative_balance` to show that when the result is true, there exists a prefix leading to a negative balance
2. It uses `false_implies_no_negative_balance` to show that when the result is false, no prefix can lead to a negative balance
3. It breaks the proof into two cases based on the return value of the implementation
4. It directly proves the problem specification by connecting the implementation's behavior to the existence of a negative balance prefix

The key steps include:
- Using `unfold problem_spec` to expose the specification definition
- Using `by_cases` to handle both true and false return values
- Applying the lemmas to derive the necessary properties
- Handling the contradiction in the false case when a negative balance prefix is claimed