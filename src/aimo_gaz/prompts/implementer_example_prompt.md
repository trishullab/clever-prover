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
∃ result, impl score_changes threshold = result →
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

[PLAN]
1. Define a recursive helper function `loop` to keep track of the running cumulative score and coins while traversing through the list of score changes. Let this helper function return the total number of coins.
2. Within this `loop` function, use a `match` statement on the remaining list of score changes.
3. If the remaining list is empty, just return the input coin count, which will be the total number of coins.
4. If not, split the list into a `head` and a `tail`. Calculate the new cumulative score using the score change at the `head` of the list, then calculate the new coin count based on whether the new cumulative score passes the threshold.
5. Still within the `match` statement, recursively call `loop` with the `tail` list of score changes and the new cumulative score and coin count.
6. Finally, outside of the `match` statement and `loop` definition, call `loop` with initial parameters. This will be the implementation function's output.
[END]

`example_assistant`
def implementation (score_changes: List Int) (threshold: Int) : Nat :=
let rec loop (score_changes: List Int) (threshold: Int) (score: Int) (coins: Nat) : Nat :=
  match score_changes with
  | [] => coins
  | head :: tail =>
    let score' := head + score
    let coins' := if score' ≥ threshold then coins + 1 else coins
    loop tail threshold score' coins'
loop score_changes threshold 0 0
