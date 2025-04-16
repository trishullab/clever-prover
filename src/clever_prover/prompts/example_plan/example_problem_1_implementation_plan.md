1. Define a recursive helper function `loop` to keep track of the running cumulative score and coins while traversing through the list of score changes. Let this helper function return the total number of coins.
2. Within this `loop` function, use a `match` statement on the remaining list of score changes.
3. If the remaining list is empty, just return the input coin count, which will be the total number of coins.
4. If not, split the list into a `head` and a `tail`. Calculate the new cumulative score using the score change at the `head` of the list, then calculate the new coin count based on whether the new cumulative score passes the threshold.
5. Still within the `match` statement, recursively call `loop` with the `tail` list of score changes and the new cumulative score and coin count.
6. Finally, outside of the `match` statement and `loop` definition, call `loop` with initial parameters. This will be the implementation function's output.