Prove a `fib0_unique` lemma that states that the 0th Fibonacci number is 0, according to `fibonacci_non_computable`.
  - Use `cases` to break apart the `fibonacci_non_computable` definition.

Prove a `fib1_unique` lemma that states that the 1st Fibonacci number is 1, according to `fibonacci_non_computable`.
  - Use `cases` to break apart the `fibonacci_non_computable` definition.

Prove a `fib_rec_unique` lemma that states the recursive property of Fibonacci numbers fully using `fibonacci_non_computable`.
  - Start by splitting the "iff".
  - Use `fibonacci_non_computable.step`.

Prove a `fib_inversion` lemma that states that the `n`th Fibonacci number is unique, according to `fibonacci_non_computable`.
  - Use strong induction on `n`.
  - Use the `fib_rec_unique` lemma.

Prove a `fib_rec_unique_seq` lemma that states that given a computable function `f : Nat → Nat` that follows the Fibonacci base cases (`f 0 = 1`, `f 1 = 1`) and recursive case (`∀ n, f (n + 2) = f n + f (n + 1)`), the built-in Lean 4 function `fibonacci_non_computable` called on `n` and `(f n)` outputs `True` (for all `n`).
  - Use induction and break the proof up into the base cases and the recursive case.

Prove the `spec_isomorphism` theorem.
  - Start by unfolding both the `problem_spec` and `generated_spec` and splitting the "iff".
  - Break the proof up into the base cases and the recursive case using `by_cases` and then `have`.
  - Use the lemmas `fib0_unique`, `fib1_unique`, `fib_inversion`, and `fib_rec_unique_seq`.
