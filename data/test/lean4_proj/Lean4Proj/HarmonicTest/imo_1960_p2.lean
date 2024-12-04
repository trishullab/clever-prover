import Mathlib

abbrev imo_1960_p2_solution : Set ℝ := sorry
-- {x : ℝ | -1 / 2 ≤ x ∧ x < 45 / 8 ∧ x ≠ 0}
theorem imo_1960_p2 (x : ℝ) : (4 * x^2 / (1 - Real.sqrt (2 * x + 1))^2 < 2 * x + 9 ∧ 0 ≤ 2 * x + 1 ∧ 1 - Real.sqrt (2 * x + 1) ≠ 0) ↔ x ∈ imo_1960_p2_solution := by
  sorry
