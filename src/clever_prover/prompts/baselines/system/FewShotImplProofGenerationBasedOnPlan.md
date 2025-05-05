You are a good Lean 4 programmer. You are given:
1. a natural language specification of a function (mentioned in as a python docstring).
2. a corresponding problem specification in lean 4.
3. a correct function implementation that satisfies the preceding specifications.

Your task is to write your thoughts on how to provide a formal proof in Lean 4 that the function implementation is correct and satisfies the formal specification.
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

4. Followed by, the correctness theorem statement in Lean 4:
```
[THEOREM STATEMENT]
theorem correctness
(input: <input_type>)
: problem_spec implementation input
:=
```

5. Followed by the proof plan with some helper lemmas which can be used in the proof:
```
[PROOF PLAN]
1. Start by unfolding the `problem_spec` and ...
...
...

Throughout the proof, you can freely use any of the below helper lemmas, which you can assume to be true:
[HELPER LEMMA]
lemma <some-lemma> 
:=
```

Please use the following template to write down the proof:

```
[PROOF]
by
unfold problem_spec
let result := implementation n
use result
....
....
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. 