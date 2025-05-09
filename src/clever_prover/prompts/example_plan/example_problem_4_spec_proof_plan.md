Prove the `spec_isomorphism` theorem.
  - Start by analyzing the generated specification. The main idea is to create a specific instance of the generated specification and show that it satisfies the properties of the problem specification and vice versa.
  - Use `by_cases` to handle the case when x = y * y and when x ≠ y * y.
  - Then simplify `if-else` statements and use an instance of the problem specification to show that the two specifications are equivalent. You might also have to show that y * y = y ^ 2, this can be done using `ring`.
  - For the reverse direction, you can use similar reasoning.
  - Introduce the `h_specialized_spec` variable to represent the specialized version of the problem specification and show that it satisfies the generated specification.
