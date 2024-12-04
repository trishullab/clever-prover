import Mathlib

open BigOperators

abbrev mathd_numbertheory_451_solution : ℕ := sorry
-- 2016
theorem mathd_numbertheory_451
  (Nice : ℕ → Prop)
  (h₀ : ∀ n, Nice n ↔ ∃ m > 0, m.divisors.card = 4 ∧ ∑ d in m.divisors, d = n) :
  ∑ n in (Finset.Icc 2010 2019).filter (fun n' : ℕ => Nice n' = true), n = mathd_numbertheory_451_solution := by
  sorry
