import Mathlib

abbrev amc12a_2003_p5_solution : ℕ := sorry
-- 14
theorem amc12a_2003_p5
  (A M C : ℕ)
  (h₀ : A < 10)
  (h₁ : M < 10)
  (h₂ : C < 10)
  (h₃ : 0 < A)
  (h₄ : Nat.ofDigits 10 [0, 1, C, M, A] + Nat.ofDigits 10 [2, 1, C, M, A] = 123422) :
  A + M + C = amc12a_2003_p5_solution := by
  sorry
