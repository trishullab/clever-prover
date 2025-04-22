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

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (score_changes: List Int) (threshold: Int) : Nat :=
sorry
[END]

[TEST CASES]
#test implementation [3, 4, -2, 1] 5 = 3
#test implementation [3, 4, 5] 5 = 2
#test implementation [3, 4, -3] 5 = 1
#test implementation [-3] (-4) = 1
[END]

`example_assistant`
1. Define a recursive helper function `loop` to keep track of the running cumulative score and coins while traversing through the list of score changes. Let this helper function return the total number of coins.
2. Within this `loop` function, use a `match` statement on the remaining list of score changes.
3. If the remaining list is empty, just return the input coin count, which will be the total number of coins.
4. If not, split the list into a `head` and a `tail`. Calculate the new cumulative score using the score change at the `head` of the list, then calculate the new coin count based on whether the new cumulative score passes the threshold.
5. Still within the `match` statement, recursively call `loop` with the `tail` list of score changes and the new cumulative score and coin count.
6. Finally, outside of the `match` statement and `loop` definition, call `loop` with initial parameters. This will be the implementation function's output.

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

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (x: Int) : Int :=
sorry
[END]

[TEST CASES]
#test implementation (-1) = 1
#test implementation 0 = 0
#test implementation 5 = 5
#test implementation (-100) = 100
#test implementation 100 = 100
[END]

`example_assistant`
The implementation is one line. If `x` is less than 0 then return `-x`, otherwise return `x`.

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

[FUNCTION IMPLEMENTATION SIGNATURE]
def implementation (n: Nat) : Nat :=
sorry
[END]

[TEST CASES]
#test implementation 0 = 1
#test implementation 1 = 1
#test implementation 2 = 2
#test implementation 3 = 3
#test implementation 4 = 5
#test implementation 5 = 8
#test implementation 6 = 13
#test implementation 7 = 21
[END]

`example_assistant`
1. Start with a `match` statement on `n` to cover both the base cases and the recursive case.
2. Cover the base cases. If `n` is 0 or `n` is 1 then output 1.
3. Finish with the recursive case. If `n` matches with `n' + 2` for a value `n'`, recursively call `implementation` on the two previous values `n'` and `n' + 1` and add the results for the output.
