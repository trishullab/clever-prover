You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a corresponding problem specification in lean 4.
3. a correct function implementation that satisfies the preceding specifications.
4. a theorem or lemma statement in Lean 4 that needs proving.
5. a detailed plan describing how to prove the theorem or lemma statement.

Your task is to write a formal proof in Lean 4 of the input theorem or lemma statement, which will be related to proving that the function implementation is correct and satisfies the formal specification.
The theorem or lemma statement is stated in the following format:
1. First we state the natural language description of the function in a docstring format:
```
[NL DESCRIPTION]
def <function_name>(<input_type>) -> <output_type>
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

4. The theorem or lemma statement in Lean 4:
```
[THEOREM STATEMENT]
theorem correctness
(input: <input_type>)
: problem_spec implementation input
:=
```

5. Finally, a detailed plan for proving the theorem or lemma statement:
```
[PROOF PLAN]
1. Start by unfolding the `problem_spec` and assigning the implementation's output to a temporary variable `result`.
2. ....
```


Write a full proof of the theorem or lemma statement in Lean 4. The proof should be in the following format:
```
[PROOF]
-- proof tactics
by
rw [...]
simp ...
-- more proof tactics
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. The proof must be in Lean 4 and should be valid. Make sure to always start your proof with `[PROOF]` followed by a `by` keyword. The proof should end with `[END]`.