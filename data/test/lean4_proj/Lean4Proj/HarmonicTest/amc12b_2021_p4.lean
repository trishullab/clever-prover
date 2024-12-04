import Mathlib

abbrev amc12b_2021_p4_solution : ℝ := sorry
-- 76
theorem amc12b_2021_p4
  (morning_mean afternoon_mean : ℝ)
  (morning_students afternoon_students : ℕ)
  (h₀ : morning_students ≠ 0)
  (h₁ : afternoon_students ≠ 0)
  (h₂ : morning_mean = 84)
  (h₃ : afternoon_mean = 70)
  (h₄ : morning_students * 4 = afternoon_students * 3) :
  (morning_students * morning_mean + afternoon_students * afternoon_mean) / (morning_students + afternoon_students) = amc12b_2021_p4_solution := by
  sorry
