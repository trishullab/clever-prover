Here's the implementation in Lean 4 following the detailed plan:

```lean
def implementation (number: Rat) : Rat :=
  number - number.floor
```

Let's break down why this implementation meets the requirements:

1. `number.floor` finds the largest integer less than or equal to the input number
2. Subtracting this floor value from the original number gives the decimal part
3. The result is always between 0 and 1 (exclusive of 1)

The function handles different scenarios:
- For 3.5, it returns 0.5
- For 4.0, it returns 0
- For 2.75, it returns 0.75

The implementation is concise and directly maps to the problem specification. It leverages Lean's built-in rational number operations to compute the decimal part of a number.

The key operations used are:
- `Rat.floor`: Returns the largest integer less than or equal to a rational number
- Subtraction: Removes the integer part, leaving only the decimal component

This implementation satisfies the problem spec by:
- Always returning a value between 0 and 1
- Ensuring that the original number equals its floor plus the returned decimal part