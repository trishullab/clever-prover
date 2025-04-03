lemma implementation_characterization (operations: List Int) :
  implementation operations = true ↔ 
    ∃ i, i ≤ operations.length ∧ (operations.take i).sum < 0 := by
  -- Define a helper statement about the process function
  let rec processChar (ops: List Int) (balance: Int) : 
    implementation.process ops balance = true ↔ 
      ∃ i, i ≤ ops.length ∧ balance + (ops.take i).sum < 0 := by
    match ops with
    | [] => 
      -- Base case: empty list
      simp [implementation.process]
      apply Iff.intro
      · intro h; contradiction
      · intro h
        rcases h with ⟨i, i_le, sum_neg⟩
        have i_eq_zero : i = 0 := by
          apply Nat.eq_zero_of_le_zero
          apply Nat.le_of_lt_succ
          rw [List.length] at i_le
          exact i_le
        rw [i_eq_zero] at sum_neg
        simp at sum_neg
        contradiction
    | op :: rest =>
      -- Inductive case: non-empty list
      simp [implementation.process]
      -- Case analysis on whether balance + op < 0
      by_cases h_neg : balance + op < 0
      · -- Case: balance + op < 0
        simp [h_neg]
        apply Iff.intro
        · intro _
          use 1
          simp
          exact h_neg
        · intro h
          simp
      · -- Case: balance + op ≥ 0
        simp [h_neg]
        -- Apply induction hypothesis for the rest of the list
        specialize processChar rest (balance + op)
        rw [processChar]
        apply Iff.intro
        · intro h
          rcases h with ⟨i, i_le, sum_neg⟩
          use i + 1
          constructor
          · simp [i_le]
          · simp
            rw [List.take_succ]
            simp
            exact sum_neg
        · intro h
          rcases h with ⟨i, i_le, sum_neg⟩
          by_cases h_i_eq_1 : i = 1
          · -- Case: i = 1
            rw [h_i_eq_1] at sum_neg
            simp at sum_neg
            contradiction
          · -- Case: i > 1
            have i_gt_0 : i > 0 := by
              cases i
              · contradiction
              · simp
            have i_ge_1 : i ≥ 1 := by linarith
            use i - 1
            constructor
            · rw [Nat.sub_le_iff_le_add i_ge_1]
              exact i_le
            · have sum_decomp : balance + (ops.take i).sum = balance + op + ((ops.take i).sum - op) := by
                rw [Int.add_sub_assoc]
                apply Int.add_left_cancel
                simp [List.take_succ_cons]
                rw [List.sum_cons]
              have take_i_minus_1 : (ops.take i).sum - op = (rest.take (i - 1)).sum := by
                rw [List.take_succ_cons]
                simp [List.sum_cons]
                rw [Int.add_sub_cancel_left]
              rw [sum_decomp] at sum_neg
              rw [take_i_minus_1] at sum_neg
              exact sum_neg

  -- Apply the helper to prove the main theorem
  unfold implementation
  exact processChar operations 0