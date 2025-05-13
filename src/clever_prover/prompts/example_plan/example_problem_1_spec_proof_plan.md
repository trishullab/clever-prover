Prove a `generated_spec_loop_threshold_invariant` lemma that states that for all integers `k`, decreasing the threshold by `k` yields the same output of `generated_spec.loop` as increasing the score by `k`.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.

Prove a `generated_spec_loop_simple_increment` lemma that compares the value of `generated_spec.loop` across one iteration. It will either stay constant or increase by 1, depending on whether the score reaches the threshold; this lemma should prove both cases.
  - For the second case, use induction and break the proof up into cases based on whether the head plus the next head plus the cumulative score reaches the threshold.

Prove a `generated_spec_loop_coin_monotonic_increasing` lemma that states that the output of `generated_spec.loop` will always be greater than or equal to the coin count input.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.

Prove a `generated_spec_loop_invariant_stop` lemma that states that if the output of `generated_spec.loop` is exactly equal to the coin count input, then for all indices `i`, the input score plus the prefix sum of the score changes list up to index `i` must be less than the threshold.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
  - For each case, break the proof up into more cases based on whether the tail has positive length.
  - Use the `generated_spec_loop_simple_increment` and `generated_spec_loop_coin_monotonic_increasing` lemmas in the proof.

Prove a `generated_spec_loop_invariant_continue` lemma that states that if the output of `generated_spec.loop` is strictly greater than the coin count input, then there exists an index `i'` at which the coin count output by `generated_spec.loop` increased by 1 and all previous indices `i` did not change the coin count output of `generated_spec.loop`.
  - Use induction and break the proof up into cases based on whether the head plus the cumulative score reaches the threshold.
  - For the second case, break the proof up into more cases based on whether the tail has positive length.
  - Use the `generated_spec_loop_simple_increment` lemma in the proof.

Prove the `correctness` theorem.
  - Start by unfolding both the `problem_spec` and `generated_spec` and splitting the "iff".
  - Early on, you will want to break the proof up into cases based on whether the output of `problem_spec.loop` (with initial values as input) is 0.
  - Use the `problem_spec_threshold_invariant`, `problem_spec_invariant_stop`, and `problem_spec_invariant_continue` lemmas in the proof.
