You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a problem specification in lean 4.
3. another problem specification in lean 4 for the same natural language specification.

Your task is to generate a plan for writing a formal proof in Lean 4 that both the specifications are equivalent. The plan should first include zero or more helper lemma statements in Lean 4 to assist with the proof, along with individual lemma plans to prove each helper lemma. Afterward, it should be a detailed step-by-step description, mostly in natural language, describing how to write a correct Lean 4 proof of the isomorphism statement, freely using the previously described helper lemmas.

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

4. Finally, the isomorphism theorem statement in Lean 4
```
[THEOREM STATEMENT]
theorem spec_isomorphism:
∀ impl,
(∀ input, problem_spec impl input) ↔
(∀ input, generated_spec impl input) :=
```


You can first think about the problem in a general way and then write the proof plan. Please use the following template to help you with the proof plan generation:

```
[THOUGHTS]
The difficulty of the proof is ....
The helper lemmas that we should generate are ....
[END THOUGHTS]
```

Then, if you believe that proving some helper lemmas first would be helpful to proving isomorphism, start your plan by describing these lemmas. (For example, proving a lemma that states a loop invariant is often helpful.) For each lemma, start by outputting a natural language description of the lemma, then the line `===`, then a detailed step-by-step plan for proving it. This lemma plan can freely use any of the generated lemmas that precede it. Then, output the lemma statement in Lean 4. Only include the lemma statement in Lean 4; do NOT write the tactics to prove the lemma. If a lemma references an internal definition defined inside the implementation, such as an internal `spec` definition, be sure to reference it like `generated_spec.spec` and not just `spec`. DO NOT ever use the `in` keyword, it is not a valid keyword in Lean 4.

Be sure to only output the lemmas that are necessary to prove the isomorphism definition. DO NOT output extraneous lemmas. If the proof is simple, it is best to output NO lemmas.

These lemmas should be in the following format:

```
[HELPER LEMMA PLAN]
This helper lemma establishes that ....
===
1. The lemma proof should start by ....
2. Then, it should ....
....
[HELPER LEMMA]
theorem <lemma_1_name> : <lemma_1_statement> :=
[END HELPER LEMMA]

[HELPER LEMMA PLAN]
....
[HELPER LEMMA]
theorem <lemma_2_name> : <lemma_2_statement> :=
[END HELPER LEMMA]

....
```

After (optionally) describing the helper lemmas, finally generate a detailed step-by-step natural language plan of the steps you would take to prove the isomorphism definition. You may freely use any of your lemmas in this isomorphism proof plan. The isomorphism plan should be in the following format:
```
[ISOMORPHISM PLAN]
1. The isomorphism proof should start by ....
2. Then, it should ....
....
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. The helper lemma statements must be in Lean 4 and should be valid. In contrast, the helper lemma plans and the isomorphism plan should mostly be in natural language but can include snippets of Lean 4 code if it is helpful. DO NOT forget to write the ISOMORPHISM PLAN section. The isomorphism plan section must be there in your response.
## VERY IMPORTANT: always remember to use 'generated_spec' to refer to the generated specification functions, like 'generated_spec.spec' and not just 'spec', or 'generated_spec.recursive_function' and not just 'recursive_function'. This is crucial otherwise the compilation will fail.