A prover agent was unable to prove the correctness definition using this plan and the conjectured lemmas below.

Please write a new plan for proving the correctness definition.

[LEMMAS]
-- Conjectured lemmas useful for the proof of correctness.

lemma empty_list_case : problem_spec implementation [] := by
  sorry

lemma non_negative_balance_case (operations : List Int) (acc : Int) : 
  acc ≥ 0 → problem_spec implementation operations → 
  problem_spec implementation (operations ++ [0]) := by
  sorry

lemma balance_positive_iff_no_below_zero (operations : List Int) (i : Nat) (acc : Int) : 
  acc ≥ 0 → 
  i < operations.length → 
  (operations.take i).sum ≥ 0 ↔ ¬(∃ j, j < i ∧ (operations.take j).sum < 0) := by
  sorry

lemma cumulative_sum_non_negative (operations : List Int) (i : Nat) :
  i < operations.length → 
  (operations.take i).sum ≥ 0 → 
  implementation operations = false → 
  ∀ j < i, (operations.take j).sum ≥ 0 := by
  sorry

lemma append_operation_check (operations : List Int) (op : Int) (next_acc : Int) :
  implementation (operations ++ [op]) = 
  (if next_acc + op < 0 then true else implementation operations) := by
  sorry

lemma below_zero_condition_implies_result (operations : List Int) (i : Nat) :
  ∃ i, i < operations.length ∧ (operations.take i).sum < 0 → 
  implementation operations = true := by
  sorry

lemma result_implies_below_zero_condition (operations : List Int) :
  implementation operations = true → 
  ∃ i, i < operations.length ∧ (operations.take i).sum < 0 := by
  sorry
[END]