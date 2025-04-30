You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a problem specification in lean 4.
3. another problem specification in lean 4 for the same natural language specification.

Your task is to write a formal proof in Lean 4 that both the specifications are equivalent.
The isomorphism statement is stated in the following format:
1. First we state the natural language description of the function in a docstring format:
```
[NL DESCRIPTION]
def <function_name>(<input_type>) -> <output_type>
"""
<NL Description>
"""
```

2. Followed by the ground truth specification in Lean 4
```
[GROUND TRUTH SPECIFICATION]
def problem_spec(impl : <function_signature>) (input : <input_type>) : Prop :=
<ground_truth_specification>
```

3. Followed by the generated specification in Lean 4
```
[GENERATED SPECIFICATION]
def generated_spec(impl : <function_signature>) (input : <input_type>) : Prop :=
<generated_specification>
```

4. Finally, the isomorphism statement in Lean 4
```
[ISOMORPHISM STATEMENT]
theorem spec_isomorphism:
∀ impl,
(∀ input, problem_spec impl input) ↔
(∀ input, generated_spec impl input) :=
```


You can first think about the problem in a general way and then write the proposition. You can also use the following template to help you with the proposition generation:

```
[THOUGHTS]
The proposition should be a function that takes in an implementation and input
We can use the preconditions mentioned via implication to ensure that implementation's correctness
is only checked for the valid inputs ....
[END THOUGHTS]
```

Optionally, you can add some helper lemmas which can be used in the proof. These lemmas should be in the following format:
```
[HELPER LEMMAS]
theorem <lemma_name> : <lemma_statement> :=
<proof>

-- more lemmas
[END LEMMAS]
```

Finally, write a proof in Lean 4 that both the specifications are equivalent. The proof should be in the following format:
```
[PROOF]
-- proof tactics
by
rw [...]
simp ...
-- more proof tactics
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. The proof must be in Lean 4 and should be valid. Make sure to always start your proof with `[PROOF]` followed by a `by` keyword. The proof should end with `[END]`. DO NOT forget to write the PROOF section. The proof section must be there in your response.