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
[END THOUGHTS]

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
[END THOUGHTS]

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