Prove a `fib_comp_to_non_comp` lemma that states that given a computable function `f : Nat → Nat` that follows the Fibonacci base cases (`f 0 = 1`, `f 1 = 1`) and recursive case (`∀ n, f (n + 2) = f n + f (n + 1)`), the built-in Lean 4 function `fibonacci_non_computable` called on `n` and `(f n)` outputs `True` (for all `n`).
  - Use induction and break the proof up into the base cases and the recursive case.

Prove the `correctness` theorem.
  - Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
  - Use the `have` keyword three times to show that `implementation` follows the three properties of the Fibonacci function:
    * `implementation 0 = 1`
    * `implementation 1 = 1`
    * `∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1)`
  - Then use these three hypotheses and the `fib_comp_to_non_comp` lemma to show that `implementation` satisfies `fibonacci_non_computable`, as required by the `spec`.
