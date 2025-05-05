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

`example_assistant`
[THOUGHTS]
We can start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
Early on, we will want to break the proof up into cases based on whether `x` is positive, negative, or zero.
Many of the intermediate goals can likely be proven using `linarith`.
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

`example_assistant`
[THOUGHTS]
We can start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
Use the `have` keyword three times to show that `implementation` follows the three properties of the Fibonacci function:
  - `implementation 0 = 1`
  - `implementation 1 = 1`
  - `∀ n', implementation (n' + 2) = implementation n' + implementation (n' + 1)`
Then use these three hypotheses to show that `implementation` satisfies `fibonacci_non_computable`, as required by the `spec`.
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

`example_assistant`
[THOUGHTS]
We should start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
Early on, we will want to break the proof up into cases based on whether the output of `implementation_loop` (with initial values as input) is 0.
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


`example_assistant`
[THOUGHTS]
We can start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
We should then simplify the goal.
Then use the `have` keyword to create a new hypothesis equating the operation of squaring a variable to that of multiplying the variable by itself.
Use this new hypothesis to rewrite the goal.
[END]

`conv end`