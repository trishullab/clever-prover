`conv start`

`example_user`
[PROBLEM STATEMENT]
/--
function_signature: "def coins_won(score_changes: List[int], threshold: int) -> int"
docstring: |
    In a game, a player's score starts at 0 and is updated round by round using values from the list
    score_changes (where positive numbers add to the score and negative numbers subtract).
    After each round, as long as the player's cumulative score is greater than or equal to the given threshold,
    the player wins a coin for that round.
    Your task is to compute and return the total number of coins won by the player by the end of the game.
test_cases:
  - input:
      score_changes:
        - 3
        - 4
        - -2
        - 1
      threshold: 5
    expected_output: 1
  - input:
      score_changes:
        - 3
        - 4
        - 5
      threshold: 5
    expected_output: 2
-/
[END]

[PROBLEM SPEC]
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
[END]

[FUNCTION IMPLEMENTATION]
def implementation (score_changes: List Int) (threshold: Int) : Nat :=
let rec loop (score_changes: List Int) (threshold: Int) (score: Int) (coins: Nat) : Nat :=
  match score_changes with
  | [] => coins
  | head :: tail =>
    let score' := head + score
    let coins' := if score' ≥ threshold then coins + 1 else coins
    loop tail threshold score' coins'
loop score_changes threshold 0 0
[END]

[CORRECTNESS DEFINITION]
theorem correctness
(score_changes: List Int)
(threshold: Int)
: problem_spec implementation score_changes threshold
:=
[END]

`example_assistant`
[LEMMA PLAN]
Prove an `implementation_loop_threshold_invariant` lemma that states that for all integers `k`, decreasing the threshold by `k` yields the same output of `implementation.loop` as increasing the score by `k`.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
[LEMMA]
lemma implementation_loop_threshold_invariant
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(k: Int)
(h_rounds_played: score_changes.length > 0)
: implementation.loop score_changes (threshold - k) score coins
= implementation.loop score_changes threshold (score + k) coins :=
[END]

[LEMMA PLAN]
Prove an `implementation_loop_simple_increment` lemma that compares the value of `implementation.loop` across one iteration. It will either stay constant or increase by 1, depending on whether the score reaches the threshold; this lemma should prove both cases.
  - For the second case, use induction and break the proof up into cases based on whether the head plus the next head plus the cumulative score reaches the threshold.
[LEMMA]
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
[END]

[LEMMA PLAN]
Prove an `implementation_loop_coin_monotonic_increasing` lemma that states that the output of `implementation.loop` will always be greater than or equal to the coin count input.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
[LEMMA]
lemma implementation_loop_coin_monotonic_increasing
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
: coins ≤ implementation.loop score_changes threshold score coins :=
[END]

[LEMMA PLAN]
Prove an `implementation_loop_invariant_stop` lemma that states that if the output of `implementation.loop` is exactly equal to the coin count input, then for all indices `i`, the input score plus the prefix sum of the score changes list up to index `i` must be less than the threshold.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
  - For each case, break the proof up into more cases based on whether the tail has positive length.
  - Use the `implementation_loop_simple_increment` and `implementation_loop_coin_monotonic_increasing` lemmas in the proof.
[LEMMA]
lemma implementation_loop_invariant_stop
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
(h_within_threshold: coins = implementation.loop score_changes threshold score coins)
: ∀ i, 1 ≤ i ∧ i ≤ score_changes.length →
score + (score_changes.take i).sum < threshold :=
[END]

[LEMMA PLAN]
Prove an `implementation_loop_invariant_continue` lemma that states that if the output of `implementation.loop` is strictly greater than the coin count input, then there exists an index `i'` at which the coin count output by `implementation.loop` increased by 1 and all previous indices `i` did not change the coin count output of `implementation.loop`.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
  - For the second case, break the proof up into more cases based on whether the tail has positive length.
  - Use the `implementation_loop_simple_increment` lemma in the proof.
[LEMMA]
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
[END]

[CORRECTNESS PLAN]
Prove the `correctness` theorem.
  - Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
  - Early on, you will want to break the proof up into cases based on whether the output of `implementation_loop` (with initial values as input) is 0.
  - Use the `implementation_loop_threshold_invariant`, `implementation_loop_invariant_stop`, and `implementation_loop_invariant_continue` lemmas in the proof.
[END]

`example_user`
[PROBLEM STATEMENT]
/--
function_signature: "def find_magnitude(x: int) -> int"
docstring: |
    Given an integer x, your task is to find the magnitude of x.
    The magnitude of an integer is defined as the absolute value of the integer.
test_cases:
  - input:
      -1
    expected_output: 1
  - input:
      0
    expected_output: 0
  - input:
      5
    expected_output: 5
-/
[END]

[PROBLEM SPEC]
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
[END]

[FUNCTION IMPLEMENTATION]
def implementation (x: Int) : Int :=
if x < 0 then -x else x
[END]

[CORRECTNESS DEFINITION]
theorem correctness
(x: Int)
: problem_spec implementation x :=
[END]

`example_assistant`
[CORRECTNESS PLAN]
Prove the `correctness` theorem.
  - Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
  - Early on, you will want to break the proof up into cases based on whether `x` is positive, negative, or zero.
  - Many of the intermediate goals can likely be proven using `linarith`.
[END]

`example_user`
[PROBLEM STATEMENT]
/--
function_signature: "def find_fibonacci(n: int) -> int"
docstring: |
    Given an integer n, your task is to find the nth Fibonacci number.
    The Fibonacci sequence is defined as follows:
    - F(0) = 1
    - F(1) = 1
    - F(n) = F(n-1) + F(n-2) for n > 1
test_cases:
  - input:
      0
    expected_output: 1
  - input:
      1
    expected_output: 1
  - input:
      2
    expected_output: 2
  - input:
      3
    expected_output: 3
  - input:
      4
    expected_output: 5
  - input:
      5
    expected_output: 8
-/
[END]

[PROBLEM SPEC]
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
[END]

[FUNCTION IMPLEMENTATION]
def implementation (n: Nat) : Nat :=
match n with
| 0 => 1
| 1 => 1
| n' + 2 => implementation n' + implementation (n' + 1)
[END]

[CORRECTNESS DEFINITION]
theorem correctness
(n: Nat)
: problem_spec implementation n
:=
[END]

`example_assistant`
[LEMMA PLAN]
Prove a `fib_comp_to_non_comp` lemma that states that given a computable function `f : Nat → Nat` that follows the Fibonacci base cases (`f 0 = 1`, `f 1 = 1`) and recursive case (`∀ n, f (n + 2) = f n + f (n + 1)`), the built-in Lean 4 function `fibonacci_non_computable` called on `n` and `(f n)` outputs `True` (for all `n`).
  - Use induction and break the proof up into the base cases and the recursive case.
[LEMMA]
lemma fib_comp_to_non_comp (n : ℕ)
(f : Nat → Nat)
(h_f_0: f 0 = 1)
(h_f_1: f 1 = 1)
(h_f_step: ∀ n, f (n + 2) = f n + f (n + 1))
: fibonacci_non_computable n (f n) :=
[END]

[CORRECTNESS PLAN]
Prove the `correctness` theorem.
  - Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
  - Use the `have` keyword three times to show that `implementation` follows the three properties of the Fibonacci function:
    * `implementation 0 = 1`
    * `implementation 1 = 1`
    * `∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1)`
  - Then use these three hypotheses and the `fib_comp_to_non_comp` lemma to show that `implementation` satisfies `fibonacci_non_computable`, as required by the `spec`.
[END]

`conv end`