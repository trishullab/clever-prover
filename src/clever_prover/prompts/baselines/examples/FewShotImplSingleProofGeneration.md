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

[THEOREM STATEMENT]
theorem correctness
(x: Int)
: problem_spec implementation x :=

[PROOF PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Early on, you will want to break the proof up into cases based on whether `x` is positive, negative, or zero.
3. Many of the intermediate goals can likely be proven using `linarith`.

`example_assistant`
[PROOF]
by
unfold problem_spec
let result := implementation x
use result
simp [result]
simp [implementation]
by_cases h_0_eq_x: x = 0
-- if x = 0 then
simp [h_0_eq_x]
by_cases h_x_lt_0: x < 0
-- if x < 0 then
simp [h_x_lt_0]
apply And.intro
linarith
apply And.intro
intro; linarith
have h_not_0_lt_x: ¬ (0 < x) := by
  linarith
intro h_x_le_0
simp [h_not_0_lt_x]
linarith
apply And.intro
simp [h_x_lt_0]
linarith
simp [h_x_lt_0]
apply And.intro
intro h_neg_x_sum
linarith
apply And.intro
have h_0_le_x: 0 ≤ x := by
  linarith
simp [h_0_le_x]
by_cases h_0_lt_x: 0 < x
-- if 0 < x then
simp [h_0_lt_x]
linarith
have h_x_eq_0: x = 0 := by
  linarith
simp [h_x_eq_0]
intro h_x_le_0
simp at h_x_lt_0
have h_x_eq_0: x = 0 := by
  linarith
contradiction
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
| 0 => 0
| 1 => 1
| n' + 2 => implementation n' + implementation (n' + 1)

[THEOREM STATEMENT]
theorem correctness
(n: Nat)
: problem_spec implementation n
:=

[PROOF PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Use the `have` keyword three times to show that `implementation` follows the three properties of the Fibonacci function:
  - `implementation 0 = 1`
  - `implementation 1 = 1`
  - `∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1)`
3. Then use these three hypotheses and the `fib_comp_to_non_comp` lemma to show that `implementation` satisfies `fibonacci_non_computable`, as required by the `spec`.

Throughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:
[HELPER LEMMAS]
[HELPER LEMMA]
lemma fib_comp_to_non_comp (n : ℕ)
(f : Nat → Nat)
(h_f_0: f 0 = 1)
(h_f_1: f 1 = 1)
(h_f_step: ∀ n, f (n + 2) = f n + f (n + 1))
: fibonacci_non_computable n (f n) :=

`example_assistant`
[PROOF]
by
unfold problem_spec
let result := implementation n
use result
simp [result]
have h_impl_n : ∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1) :=
by
  intro n'
  rw [implementation]
have h_impl_0 : implementation 0 = 0 := by
  rw [implementation]
have h_impl_1 : implementation 1 = 1 := by
  rw [implementation]
apply fib_comp_to_non_comp
all_goals assumption
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

[THEOREM STATEMENT]
theorem correctness
(score_changes: List Int)
(threshold: Int)
: problem_spec implementation score_changes threshold
:=

[PROOF PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Early on, you will want to break the proof up into cases based on whether the output of `implementation.loop` (with initial values as input) is 0.
3. Use the `implementation_loop_threshold_invariant`, `implementation_loop_invariant_stop`, and `implementation_loop_invariant_continue` lemmas in the proof.

Throughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:
[HELPER LEMMAS]
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
[HELPER LEMMA]
lemma implementation_loop_coin_monotonic_increasing
(score_changes: List Int)
(threshold: Int)
(score: Int)
(coins: Nat)
(h_rounds_played: score_changes.length > 0)
: coins ≤ implementation.loop score_changes threshold score coins :=
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

`example_assistant`
[PROOF]
by
-- sometimes we have to create a temporary variable to use in the proof
unfold problem_spec
let result := implementation score_changes threshold
use result
simp [result]
simp [implementation]
intros h_rounds_played
have h_stop := implementation_loop_invariant_stop score_changes threshold 0 0 h_rounds_played
by_cases h_implementation_stop: implementation.loop score_changes threshold 0 0 = 0
-- Case 1: where implementation.loop score_changes threshold 0 0 = 0
simp [h_implementation_stop]
simp [h_implementation_stop] at h_stop
exact h_stop
-- Case 2: where implementation.loop score_changes threshold 0 0 ≠ 0
simp [h_implementation_stop]
have h_implementation_stop': 0 < implementation.loop score_changes threshold 0 0 := by
  by_contra
  rename_i h_implementation_stop_false
  simp at h_implementation_stop_false
  contradiction
have h_continue := implementation_loop_invariant_continue score_changes threshold 0 0 h_rounds_played h_implementation_stop'
simp at h_continue
obtain ⟨i₁⟩ := h_continue
rename_i h_continue_i₁
use i₁
intro h_1_le_i₁ h_iᵢ_score_len h_threshold
simp [h_1_le_i₁, h_iᵢ_score_len, h_threshold] at h_continue_i₁
by_cases h_drop_i₁: (List.drop i₁ score_changes).length > 0
have h_threshold' := implementation_loop_threshold_invariant (List.drop i₁ score_changes) threshold 0 0 (List.take i₁ score_changes).sum h_drop_i₁
simp at h_threshold'
simp [h_threshold']
intro h_drop_impl
simp [h_drop_impl] at h_continue_i₁
intro i''
intro h_i''_le_i₁
have h'' := h_continue_i₁ i''
by_cases h_1_le_i'': 1 ≤ i''
simp [h_1_le_i''] at h''
assumption
simp at h_1_le_i''
linarith
simp at h_drop_i₁
have h_i₁_eq_score_changes_len : i₁ = score_changes.length := by
  linarith
simp [h_i₁_eq_score_changes_len] at h_continue_i₁
simp [implementation.loop] at h_continue_i₁
simp [h_i₁_eq_score_changes_len]
simp [implementation.loop]
exact h_continue_i₁
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

[THEOREM STATEMENT]
theorem correctness
(x: Int)
(y: Int)
: problem_spec implementation x y:=

[PROOF PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. Simplify the goal.
3. Use the `have` keyword to create a new hypothesis equating the operation of squaring a variable to that of multiplying the variable by itself.
4. Use this new hypothesis to rewrite the goal.

`example_assistant`
[PROOF]
by
unfold problem_spec
let result := implementation x y
use result
simp [result]
simp [implementation]
have h_eq: y ^ 2 = y * y := by ring
rw [h_eq]
[END]

`conv end`