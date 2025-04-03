```lean
lemma floor_le_self (n: Rat) : n.floor ≤ n := by
  sorry

lemma self_lt_floor_plus_one (n: Rat) : n < n.floor + 1 := by
  sorry

lemma truncated_nonnegative (n: Rat) : n - n.floor ≥ 0 := by
  sorry

lemma truncated_lt_one (n: Rat) : n - n.floor < 1 := by
  sorry

lemma decomposition_property (n: Rat) : n = n.floor + (n - n.floor) := by
  sorry

lemma implementation_satisfies_spec (n: Rat) : 
  let result := implementation n
  0 ≤ result ∧ result < 1 ∧ n = n.floor + result := by
  sorry
```