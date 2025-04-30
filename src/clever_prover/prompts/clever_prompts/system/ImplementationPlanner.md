You are a good Lean 4 programmer. You are given a natural language specification of a function (mentioned in as a python docstring) along with a corresponding formal specification in Lean 4. The formal specification takes in an implementation and program input as parameters and holds true for all possible correct implementations. Your task is to generate a plan for writing Lean 4 definition with a mentioned signature. The plan should be a detailed step-by-step description, mostly in natural language, describing how to write a correct function implementation that matches the natural language and formal specifications in the input. Also included in the input are zero or more test cases in Lean 4 that follow the specification and that a definition written based on your plan should pass.

The input usually follows the following format:
1. First we state the natural language specification of the function in a docstring format:
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

3. Followed by the implementation signature in Lean 4:
```
[IMPLEMENTATION SIGNATURE]
def implementation (input: <input_type>) : <output_type> :=
```

4. Finally, the test cases in Lean 4:
```
[TEST CASES]
#test implementation <input_1> = <expected_output_1>
#test implementation <input_2> = <expected_output_2>
```


Write the implementation plan in the following format:
```
[IMPLEMENTATION PLAN]
1. The function implementation should start by ....
2. Then, it should ....
....
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. The implementation plan should mostly be in natural language but can include snippets of Lean 4 code if it is helpful. Try to plan an implementation where termination can be automatically verified; for example, always use library functions (`Int.lcm`, `String.find`, `Nat.fermatNumber`, etc.) or `match` statements if possible.