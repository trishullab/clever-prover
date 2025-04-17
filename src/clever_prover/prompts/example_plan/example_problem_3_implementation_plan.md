1. Start with a `match` statement on `n` to cover both the base cases and the recursive case.
2. Cover the base cases. If `n` is 0 or `n` is 1 then output 1.
3. Finish with the recursive case. If `n` matches with `n' + 2` for a value `n'`, recursively call `implementation` on the two previous values `n'` and `n' + 1` and add the results for the output.
