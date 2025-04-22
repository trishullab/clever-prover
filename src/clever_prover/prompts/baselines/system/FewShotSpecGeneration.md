You are a good Lean 4 programmer. You are given a natural language specification of a function (mentioned in as a python docstring). Your task is to generate a Lean 4 proposition with a mentioned signature. The proposition takes in an implementation and program input as parameters. The proposition should hold true for all possible inputs in the domain, which means any preconditions should be mentioned in the specification to ensure that those cases are handled appropriately and hence the proposition is always valid if the implementation is correct.

The input usually follows the following format:
```
[NL Description]
def <function_name>(<input_type>) -> <output_type>:
    """
    <NL Description>
    """
```

Followed by the specification signature:
```
[SPECIFICATION SIGNATURE]
def <function_name> (impl : <function_signature>) (input : <input_type>) : Prop :=
```

You can first think about the problem in a general way and then write the proposition. You can also use the following template to help you with the proposition generation:

```
[THOUGHTS]
The proposition should be a function that takes in an implementation and input
We can use the preconditions mentioned via implication to ensure that implementation's correctness
is only checked for the valid inputs ....
[END THOUGHTS]
```

Followed by some optional Lean 4 helper definitions which can be used while writing the proposition:
```
[HELPER DEFINITIONS]
-- Optional helper definitions
def <some_helper> : <type> := <value>
[END DEFINITIONS]
```

Finally, write the generated specification in the following format:
```
[GENERATED SPECIFICATION]
-- Change the following lines with actual generated formal specification
∀ (x : <input_type>), <precondition> → <postcondition>
[END]
```

Please closely follow the format as shown in the examples below. Make sure that your response always ends with [END]. Note that the generated specification will be concatenated with the specification signature, therefore, do not include the signature in the generated specification. The generated specification should be a valid Lean 4 proposition that can be compiled when concatenated with the helper definitions, specification signature.