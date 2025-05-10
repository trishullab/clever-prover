You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a corresponding problem specification in lean 4.
3. a correct function implementation that satisfies the preceding specifications.

Your task is to generate a plan for writing a formal proof in Lean 4 that the function implementation is correct and satisfies the formal specification. The plan should first include zero or more helper lemma statements in Lean 4 to assist with the proof, along with individual lemma plans to prove each helper lemma. Afterward, it should be a detailed step-by-step description, mostly in natural language, describing how to write a correct Lean 4 proof of the correctness statement, freely using the previously described helper lemmas.

The correctness statement is stated in the following format:
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

4. Finally, the correctness theorem statement in Lean 4:
```
[THEOREM STATEMENT]
theorem correctness
(input: <input_type>)
: problem_spec implementation input
:=
```


You can first think about the problem in a general way and then write the proof plan. Please use the following template to help you with the proof plan generation:

```
[THOUGHTS]
The difficulty of the proof is ....
The helper lemmas that we should generate are ....
[END THOUGHTS]
```

Then, if you believe that proving some helper lemmas first would be helpful to proving correctness, start your plan by describing these lemmas. (For example, proving a lemma that states a loop invariant is often helpful.) For each lemma, start by outputting a natural language description of the lemma, then the line `===`, then a detailed step-by-step plan for proving it. This lemma plan can freely use any of the generated lemmas that precede it. Then, output the lemma statement in Lean 4. Only include the lemma statement in Lean 4; do NOT write the tactics to prove the lemma. If a lemma references an internal definition defined inside the implementation, such as a recursive `loop` definition, be sure to reference it like `implementation.loop` and not just `loop`. DO NOT ever use the `in` keyword, it is not a valid keyword in Lean 4.

Be sure to only output the lemmas that are necessary to prove the correctness definition. DO NOT output extraneous lemmas. If the proof is simple, it is best to output NO lemmas.

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

After (optionally) describing the helper lemmas, finally generate a detailed step-by-step natural language plan of the steps you would take to prove the correctness definition. You may freely use any of your lemmas in this correctness proof plan. The correctness plan should be in the following format:
```
[CORRECTNESS PLAN]
1. The correctness proof should start by ....
2. Then, it should ....
....
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. The helper lemma statements must be in Lean 4 and should be valid. In contrast, the helper lemma plans and the correctness plan should mostly be in natural language but can include snippets of Lean 4 code if it is helpful. DO NOT forget to write the CORRECTNESS PLAN section. The correctness plan section must be there in your response.
## VERY IMPORTANT: always remember to use 'implemenation' to refer to the implementation functions, like 'implementation.loop' and not just 'loop', or 'implementation.recursive_function' and not just 'recursive_function'. This is crucial otherwise the compilation will fail.
## VERY IMPORTANT: Usually the helper lemmas refer to the recursive function defined in the implementation, the ones with `let rec` keyword. You will not be able to refer any other `let` definitions within the `implementation`. Only those defined with `let rec` keyword should be used while writing the helper lemmas.