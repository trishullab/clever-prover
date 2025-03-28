Here's the implementation of the `implementation` function for truncating a number to its decimal part in Lean 4:

```lean
def implementation (number: Rat) : Rat :=
  number - number.floor
```

This concise implementation follows the plan exactly:
1. It takes a rational number as input
2. Uses `number.floor` to get the integer part
3. Subtracts the floor value from the original number
4. Returns the decimal part (which is always less than 1)

Let's verify it meets the requirements:
- It works for positive rational numbers
- Returns only the decimal portion 
- Handles whole numbers by returning 0
- Leverages Lean 4's built-in rational number operations

The implementation can be verified with the provided test case:
```lean
#test implementation 3.5 = 0.5
```

This solution is simple, direct, and leverages Lean 4's built-in rational number capabilities to solve the problem efficiently.