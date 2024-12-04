import Mathlib

abbrev amc12a_2021_p25_solution : ℕ := sorry
-- 9
theorem amc12a_2021_p25
  (f : ℕ → ℝ)
  (h₀ : ∀ n, f n = (n.divisors.card : ℝ) / n^(1 / 3 : ℝ))
  (N : ℕ)
  (hN : ∀ n ≠ N, f N > f n) :
  (N.digits 10).sum = amc12a_2021_p25_solution := by
  sorry
