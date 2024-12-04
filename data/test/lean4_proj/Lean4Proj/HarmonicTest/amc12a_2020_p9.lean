import Mathlib

abbrev amc12a_2020_p9_solution : ℕ := sorry
-- 5
theorem amc12a_2020_p9 :
  Set.ncard {x : ℝ | x ∈ Set.Icc 0 (2 * Real.pi) ∧ Real.tan (2 * x) = Real.cos (x / 2)} = amc12a_2020_p9_solution := by
  sorry
