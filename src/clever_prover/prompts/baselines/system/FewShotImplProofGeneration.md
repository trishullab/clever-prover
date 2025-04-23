You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a corresponding problem specification in lean 4.
3. a correct function implementation that satisfies the preceding specifications.

Your task is to write a formal proof in Lean 4 that the function implementation is correct and satisfies the formal specification.
The correctness statement is stated in the following format:
1. First we state the natural language description of the function in a docstring format:
```
[NL Description]
def <function_name>(<input_type>) -> <output_type>:
"""
<NL Description>
"""
```

2. Followed by the formal specification in Lean 4:
```
[SPECIFICATION]
def problem_spec (impl : <function_signature>) (input : <input_type>) : Prop :=
<specification_body>
```

3. Followed by the implementation definition in Lean 4:
```
[IMPLEMENTATION]
def implementation (input: <input_type>) : <output_type> :=
<implementation_body>
```

4. Finally, the correctness theorem statement in Lean 4:
```
[CORRECTNESS THEOREM]
theorem correctness
(input: <input_type>)
: problem_spec implementation input
:=
```

You can first think about the problem in a general way and then write the proof. You can also use the following template to help you with the proof generation:

```
[THOUGHTS]
The implementation should match the problem_spec in the first case because
The implementation should match the problem_spec in the second case because ....
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


Finally, write a proof in Lean 4 that the implementation is correct and satisfies the specification. The proof should be in the following format:
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