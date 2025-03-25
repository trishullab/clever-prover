To implement the `truncate_number` function in Lean 4, we need to break down the task into a series of logical steps that will guide us through the process of coding and validating our solution. Here's a detailed plan:

1. **Understand the Problem Statement**: The task is to create a function that takes a positive floating-point number (represented in Lean as a `Rat`, which denotes a rational number), and returns its decimal part after separating it from the integer part.

2. **Analyze the Requirements**: The primary requirement is to:
   - Get the largest integer smaller than the given number. This is typically done using a function that returns the floor of the number.
   - Subtract this integer part from the original number to get the decimal (or fractional) part.
   
3. **Define the Function Signature**: We need to implement the function with the provided signature:
   ```lean
   def implementation (number: Rat) : Rat :=
   ```
   Here, `number` will be a positive rational number (float), and the function should return another `Rat` representing the decimal part.

4. **Determine the Mathematical Operations**:
   - Use the `floor` function to get the integer part of the number.
   - Subtract the integer part obtained from `number` to derive the decimal part. 

5. **Draft the Actual Code Logic**:
   - First, compute `integer_part` as `number.floor`.
   - Then, define the `decimal_part` as `number - integer_part`.
   - Finally, return `decimal_part`.

6. **Consider Edge Cases**: The problem specifies that the input number is always positive, so edge cases are minimal. However, we should consider very small float values (close to zero) to ensure our subtraction doesn't lead to unexpected results.

7. **Implement the Function**: Based on our understanding and planned logic, the code would look something like this:
   ```lean
   def implementation (number: Rat) : Rat :=
     let integer_part := number.floor
     let decimal_part := number - integer_part
     decimal_part
   ```

8. **Verify Against Test Cases**: Use the given test case (i.e., input `3.5` should return `0.5`) to manually verify that the function works correctly. We can directly call the function in the Lean 4 REPL or test environment:
   ```lean
   #eval implementation 3.5  -- should yield 0.5
   ```

9. **Formal Validation**: Finally, ensure that the implementation adheres to the function specification stated in the problem spec. Using the `spec` defined, we should verify that for the computed output, it satisfies `res = number - number.floor`.

10. **Complete and Document**: After confirming that everything is working as expected, we should add comments and documentation to clarify how the function operates, reflecting the logic applied.

By following these steps, we can confidently implement `truncate_number` to deliver the desired results while also ensuring correctness through specifications and test cases.