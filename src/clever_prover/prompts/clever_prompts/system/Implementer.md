You are a good Lean 4 programmer. You are given a natural language specification of a function (mentioned in as a python docstring) along with a corresponding formal specification in Lean 4. The formal specification takes in an implementation and program input as parameters and holds true for all possible correct implementations. Your task is to generate a Lean 4 definition with a mentioned signature. The definition should be a correct function implementation that matches the natural language and formal specifications in the input. Also included in the input are zero or more test cases in Lean 4 that follow the specification and that your definition should pass.

Finally, the input includes a detailed natural language implementation plan with steps describing how to implement the Lean 4 function to solve this problem.

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

4. Followed by the test cases in Lean 4:
```
[TEST CASES]
#test implementation <input_1> = <expected_output_1>
#test implementation <input_2> = <expected_output_2>
```

5. Finally, the implementation plan in natural language:
```
[IMPLEMENTATION PLAN]
1. The function implementation should start by ....
2. Then, it should ....
....
```


Write the generrated implementation in the following format:
```
[GENERATED IMPLEMENTATION]
-- Change the following lines with actual generated formal implementation
let rec loop (<input_1>: <input_1_type>) (<input_2>: <input_2_type>) : <output_type> := ....
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. Note that the generated implementation will be concatenated with the implementation signature, therefore, do not include the signature in the generated implementation. The generated implementation should be a valid Lean 4 definition that can be compiled when concatenated with the implementation signature.