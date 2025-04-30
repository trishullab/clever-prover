`conv start`

`example_user`
[NL DESCRIPTION]
def find_magnitude(x: int) -> int
"""
Given an integer x, your task is to find the magnitude of x.
The magnitude of an integer is defined as the absolute value of the integer.
"""

[SPECIFICATION]
def problem_spec
-- function signature
(impl: Int → Int)
-- inputs
(x: Int) :=
-- spec
let spec (result: Int) :=
(result ≥ 0) ∧
(impl (-x) = result) ∧
(result = 0 ↔ x = 0) ∧
(0 ≤ x → impl (-x) + result = 2 * x) ∧
(x ≤ 0 → impl (-x) + result = -2 * x)
-- program terminates
∃ result, impl x = result ∧
-- return value satisfies spec
spec result

[IMPLEMENTATION]
def implementation (x: Int) : Int :=
if x < 0 then -x else x

[CORRECTNESS THEOREM]
theorem correctness
(x: Int)
: problem_spec implementation x :=

`example_assistant`
[CORRECTNESS PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Early on, you will want to break the proof up into cases based on whether `x` is positive, negative, or zero.
3. Many of the intermediate goals can likely be proven using `linarith`.
[END]


`example_user`
[NL DESCRIPTION]
def find_fibonacci(n: int) -> int
"""
Given an integer n, your task is to find the nth Fibonacci number.
The Fibonacci sequence is defined as follows:
- F(0) = 1
- F(1) = 1
- F(n) = F(n-1) + F(n-2) for n > 1
"""

[SPECIFICATION]
def problem_spec
-- function signature
(impl: Nat → Nat)
-- inputs
(n: Nat) :=
-- spec
let spec (result: Nat) :=
fibonacci_non_computable n result
-- program terminates
∃ result, impl n = result ∧
-- return value satisfies spec
spec result

[IMPLEMENTATION]
def implementation (n: Nat) : Nat :=
match n with
| 0 => 1
| 1 => 1
| n' + 2 => implementation n' + implementation (n' + 1)

[CORRECTNESS THEOREM]
theorem correctness
(n: Nat)
: problem_spec implementation n
:=

`example_assistant`
[HELPER LEMMA PLAN]
Prove a `fib_comp_to_non_comp` lemma that states that given a computable function `f : Nat → Nat` that follows the Fibonacci base cases (`f 0 = 1`, `f 1 = 1`) and recursive case (`∀ n, f (n + 2) = f n + f (n + 1)`), the built-in Lean 4 function `fibonacci_non_computable` called on `n` and `(f n)` outputs `True` (for all `n`).
1. Use induction and break the proof up into the base cases and the recursive case.
[HELPER LEMMA]
lemma fib_comp_to_non_comp (n : ℕ)
(f : Nat → Nat)
(h_f_0: f 0 = 1)
(h_f_1: f 1 = 1)
(h_f_step: ∀ n, f (n + 2) = f n + f (n + 1))
: fibonacci_non_computable n (f n) :=
[END HELPER LEMMA]

[CORRECTNESS PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Use the `have` keyword three times to show that `implementation` follows the three properties of the Fibonacci function:
  - `implementation 0 = 1`
  - `implementation 1 = 1`
  - `∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1)`
3. Then use these three hypotheses and the `fib_comp_to_non_comp` lemma to show that `implementation` satisfies `fibonacci_non_computable`, as required by the `spec`.
[END]


`example_user`
[NL DESCRIPTION]
def coins_won(score_changes: List[int], threshold: int) -> int
"""
In a game, a player's score starts at 0 and is updated round by round using values from the list
score_changes (where positive numbers add to the score and negative numbers subtract).
After each round, as long as the player's cumulative score is greater than or equal to the given threshold,
the player wins a coin for that round.
Your task is to compute and return the total number of coins won by the player by the end of the game.
"""

[SPECIFICATION]
def problem_spec
-- function signature
(impl: List Int → Int → Nat)
-- inputs
(score_changes: List Int)
(threshold: Int) :=
-- spec
let spec (score_changes' : List Int) (threshold' : Int) (result: Nat) :=
score_changes'.length > 0 →
if result = 0 then
  ∀ i, 1 ≤ i ∧ i ≤ score_changes'.length →
  (score_changes'.take i).sum < threshold'
else
  (∃ i, 1 ≤ i ∧ i ≤ score_changes'.length →
  (score_changes'.take i).sum ≥ threshold' →
  ( let score_changes'' := score_changes'.drop i;
    let threshold'' := threshold' - (score_changes'.take i).sum;
    let result' := impl score_changes'' threshold'';
    result = 1 + result') →
  ∀ i', 1 ≤ i' ∧ i' < i → (score_changes'.take i').sum < threshold
  );
-- program terminates
∃ result, impl score_changes threshold = result ∧
-- return value satisfies spec
spec score_changes threshold result

[IMPLEMENTATION]
def implementation (score_changes: List Int) (threshold: Int) : Nat :=
let rec loop (score_changes: List Int) (threshold: Int) (score: Int) (coins: Nat) : Nat :=
  match score_changes with
  | [] => coins
  | head :: tail =>
    let score' := head + score
    let coins' := if score' ≥ threshold then coins + 1 else coins
    loop tail threshold score' coins'
loop score_changes threshold 0 0

[CORRECTNESS THEOREM]
theorem correctness
(score_changes: List Int)
(threshold: Int)
: problem_spec implementation score_changes threshold
:=

`example_assistant`
[HELPER LEMMA PLAN]
Prove an `implementation_loop_threshold_invariant` lemma that states that for all integers `k`, decreasing the threshold by `k` yields the same output of `implementation.loop` as increasing the score by `k`.
1. Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
[HELPER LEMMA]
lemma implementation_loop_threshold_invariant
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(k: Int)
(h_rounds_played: score_changes.length > 0)
: implementation.loop score_changes (threshold - k) score coins
= implementation.loop score_changes threshold (score + k) coins :=
[END HELPER LEMMA]

[HELPER LEMMA PLAN]
Prove an `implementation_loop_simple_increment` lemma that compares the value of `implementation.loop` across one iteration. It will either stay constant or increase by 1, depending on whether the score reaches the threshold; this lemma should prove both cases.
1. For the second case, use induction and break the proof up into cases based on whether the head plus the next head plus the cumulative score reaches the threshold.
[HELPER LEMMA]
lemma implementation_loop_simple_increment
(head: Int)
(score_changes_tail: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
: (head + score < threshold →
implementation.loop (head :: score_changes_tail) threshold score coins =
implementation.loop (score_changes_tail) threshold (head + score) coins) ∧
(head + score ≥ threshold →
implementation.loop (head :: score_changes_tail) threshold score coins =
1 + implementation.loop (score_changes_tail) threshold (head + score) coins) :=
[END HELPER LEMMA]

[HELPER LEMMA PLAN]
Prove an `implementation_loop_coin_monotonic_increasing` lemma that states that the output of `implementation.loop` will always be greater then or equal to the coin count input.
1. Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
[HELPER LEMMA]
lemma implementation_loop_coin_monotonic_increasing
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
: coins ≤ implementation.loop score_changes threshold score coins :=
[END HELPER LEMMA]

[HELPER LEMMA PLAN]
Prove an `implementation_loop_invariant_stop` lemma that states that if the output of `implementation.loop` is exactly equal to the coin count input, then for all indices `i`, the input score plus the prefix sum of the score changes list up to index `i` must be less than the threshold.
1. Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
2. For each case, break the proof up into more cases based on whether the tail has positive length.
3. Use the `implementation_loop_simple_increment` and `implementation_loop_coin_monotonic_increasing` lemmas in the proof.
[HELPER LEMMA]
lemma implementation_loop_invariant_stop
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins = implementation.loop score_changes threshold score coins)
: ∀ i, 1 ≤ i ∧ i ≤ score_changes.length →
score + (score_changes.take i).sum < threshold :=
[END HELPER LEMMA]

[HELPER LEMMA PLAN]
Prove an `implementation_loop_invariant_continue` lemma that states that if the output of `implementation.loop` is strictly greater than the coin count input, then there exists an index `i'` at which the coin count output by `implementation.loop` increased by 1 and all previous indices `i` did not change the coin count output of `implementation.loop`.
1. Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
2. For the second case, break the proof up into more cases based on whether the tail has positive length.
3. Use the `implementation_loop_simple_increment` lemma in the proof.
[HELPER LEMMA]
lemma implementation_loop_invariant_continue
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins < implementation.loop score_changes threshold score coins)
:∃ i', 1 ≤ i' ∧ i' ≤ score_changes.length →
(score + (score_changes.take i').sum ≥ threshold) →
implementation.loop score_changes threshold score coins =
1 + implementation.loop (score_changes.drop i') threshold
(score + (score_changes.take i').sum) coins →
∀ i, 1 ≤ i ∧ i < i' → score + (score_changes.take i).sum < threshold :=
[END HELPER LEMMA]

[CORRECTNESS PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Early on, you will want to break the proof up into cases based on whether the output of `implementation_loop` (with initial values as input) is 0.
3. Use the `implementation_loop_threshold_invariant`, `implementation_loop_invariant_stop`, and `implementation_loop_invariant_continue` lemmas in the proof.
[END]


`example_user`
[NL DESCRIPTION]
def is_square(x: int, y: int) -> bool
"""
Given two integers x and y, your task is to find if x is a square of y.
The function should return true if x is a square of y, otherwise false.
"""

[SPECIFICATION]
def problem_spec
-- function signature
(impl: Int → Int → Bool)
-- inputs
(x: Int)
(y: Int) :=
-- spec
let spec (result: Bool) :=
result = true ↔ x = y^2;
-- program terminates
∃ result, impl x y = result ∧
-- return value satisfies spec
spec result

[IMPLEMENTATION]
def implementation (x: Int) (y: Int) : Bool :=
if x = y * y then
  true
else
  false

[CORRECTNESS THEOREM]
theorem correctness
(x: Int)
(y: Int)
: problem_spec implementation x y:=

`example_assistant`
[CORRECTNESS PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Simplify the goal.
3. Use the `have` keyword to create a new hypothesis equating the operation of squaring a variable to that of multiplying the variable by itself.
4. Use this new hypothesis to rewrite the goal.
[END]

`conv end`