lemma process_below_zero_equiv
(ops: List Int)
(balance: Int)
: implementation.process ops balance = true ↔
  ∃ i, i ≤ ops.length ∧ (balance + (ops.take i).sum < 0) := by
  induction ops generalizing balance
  case nil =>
    -- For empty list, process always returns false
    simp [implementation.process]
    
    -- Prove both directions of the equivalence
    apply Iff.intro
    
    -- Forward direction (false → ∃i...)
    intro h
    contradiction
    
    -- Backward direction (∃i... → false)
    intro h
    cases h with | intro i h' =>
    cases h' with | intro h_i_le_length h_sum_negative =>
    -- If i ≤ 0, then i must be 0
    have h_i_eq_0 : i = 0 := by
      simp at h_i_le_length
      exact Nat.eq_zero_of_le_zero h_i_le_length
    subst h_i_eq_0
    -- But then balance must be negative, contradicting our premise
    simp at h_sum_negative
    contradiction
    
  case cons op rest ih =>
    -- Expand the definition of process for cons case
    simp [implementation.process]
    
    -- Split into cases based on whether balance + op < 0
    by_cases h_new_balance_negative : balance + op < 0
    
    -- Case 1: balance + op < 0, process immediately returns true
    {
      simp [h_new_balance_negative]
      
      apply Iff.intro
      
      -- Forward direction (true → ∃i...)
      intro _
      -- Choose i=1 which shows the condition is satisfied
      exists 1
      simp [List.take]
      exact h_new_balance_negative
      
      -- Backward direction (∃i... → true)
      intro _
      trivial
    }
    
    -- Case 2: balance + op ≥ 0, process continues recursively
    {
      simp [h_new_balance_negative]
      
      -- Use induction hypothesis with updated balance
      specialize ih (balance + op)
      rw [ih]
      
      apply Iff.intro
      
      -- Forward direction
      intro ⟨i, h_i_le_len, h_sum_negative⟩
      -- For i from the rest list, we use i+1 for the full list
      exists i + 1
      constructor
      · simp; exact Nat.succ_le_succ h_i_le_len
      · -- Need to show that balance + (op::rest).take(i+1).sum < 0
        have h_take_eq : (op :: rest).take (i + 1) = op :: rest.take i := by
          rw [List.take_cons_succ]
        simp [h_take_eq]
        exact h_sum_negative
      
      -- Backward direction
      intro ⟨i, h_i_le_len, h_sum_negative⟩
      
      -- Consider cases for i
      by_cases h_i_eq_0 : i = 0
      { -- If i=0, then sum is just balance which isn't negative
        subst h_i_eq_0
        simp at h_sum_negative
        contradiction
      }
      
      by_cases h_i_eq_1 : i = 1
      { -- If i=1, then sum is balance + op which isn't negative
        subst h_i_eq_1
        simp at h_sum_negative
        simp [List.take] at h_sum_negative
        contradiction
      }
      
      -- If i > 1, we can use i-1 for the rest list
      have h_i_gt_1 : i > 1 := by
        apply Nat.gt_of_not_le
        intro h
        have h_i_le_1 : i ≤ 1 := h
        have h_i_eq_0_or_1 : i = 0 ∨ i = 1 := by
          apply Nat.eq_zero_or_eq_one_of_le_one h_i_le_1
        cases h_i_eq_0_or_1 <;> contradiction
      
      exists i - 1
      constructor
      { -- Show i-1 ≤ rest.length
        simp at h_i_le_len
        linarith
      }
      { -- Show the sum condition for rest with i-1
        have h_take_i : (op :: rest).take i = op :: rest.take (i - 1) := by
          rw [List.take_cons_succ]
          exact Nat.lt_of_succ_lt (Nat.succ_lt_succ h_i_gt_1)
        rw [h_take_i] at h_sum_negative
        simp at h_sum_negative
        -- Need to show: (balance + op) + (rest.take (i-1)).sum < 0
        exact h_sum_negative
      }
    }