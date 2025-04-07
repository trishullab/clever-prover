Let's approach this proof systematically.

[CORRECTNESS PLAN]
1. The proof for this problem is relatively straightforward since the implementation directly calculates the decimal part by subtracting the floor from the original number.

2. We need to prove three key parts of the specification:
   a) The result is non-negative (0 ≤ res)
   b) The result is less than 1 (res < 1)
   c) The original number can be reconstructed by adding the floor and the result (number = number.floor + res)

3. Key steps in the proof:
   - Unfold the problem_spec definition
   - Use properties of rat.floor()
   - Leverage mathematical properties of subtraction between a number and its floor

4. Specific tactics I would use:
   - `apply And.intro` to break down the conjunctive spec
   - `simp` to simplify floor and subtraction expressions
   - Use `Rat.sub_floor` or similar built-in lemmas about rational number floors
[END]

This problem has a very direct solution because the implementation exactly captures the mathematical definition of getting the decimal part of a number. The proof should be relatively simple and rely on fundamental properties of rational number floors.

The key is to prove that `number - number.floor` meets all three conditions: 
1. Being non-negative
2. Being less than 1
3. Reconstructing the original number when added back to its floor

Would you like me to elaborate on any part of this proof strategy?