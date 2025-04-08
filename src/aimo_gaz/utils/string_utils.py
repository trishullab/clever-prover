import typing

def parse_problem_file(raw_problem: str) -> typing.Tuple[str, str, str, str, str]:
    PROBLEM_STATEMENT_START_STRING = "-- start_def problem_details"
    PROBLEM_STATEMENT_END_STRING = "-- end_def problem_details"
    PROBLEM_SPEC_START_STRING = "-- start_def problem_spec"
    PROBLEM_SPEC_END_STRING = "-- end_def problem_spec"
    IMPLEMENTATION_SIGNATURE_START_STRING = "-- start_def implementation_signature"
    IMPLEMENTATION_SIGNATURE_END_STRING = "-- end_def implementation_signature"
    TEST_CASES_START_STRING = "-- start_def test_cases"
    TEST_CASES_END_STRING = "-- end_def test_cases"
    CORRECTNESS_DEFINITION_START_STRING = "-- start_def correctness_definition"
    CORRECTNESS_DEFINITION_END_STRING = "-- end_def correctness_definition"
    
    problem_statement_start_ind = raw_problem.find(PROBLEM_STATEMENT_START_STRING)
    problem_statement_end_ind = raw_problem.find(PROBLEM_STATEMENT_END_STRING)
    problem_spec_start_ind = raw_problem.find(PROBLEM_SPEC_START_STRING)
    problem_spec_end_ind = raw_problem.find(PROBLEM_SPEC_END_STRING)
    implementation_signature_start_ind = raw_problem.find(IMPLEMENTATION_SIGNATURE_START_STRING)
    implementation_signature_end_ind = raw_problem.find(IMPLEMENTATION_SIGNATURE_END_STRING)
    test_cases_start_ind = raw_problem.find(TEST_CASES_START_STRING)
    test_cases_end_ind = raw_problem.find(TEST_CASES_END_STRING)
    correctness_definition_start_ind = raw_problem.find(CORRECTNESS_DEFINITION_START_STRING)
    correctness_definition_end_ind = raw_problem.find(CORRECTNESS_DEFINITION_END_STRING)

    if problem_statement_start_ind == -1 or problem_statement_end_ind == -1 \
            or problem_spec_start_ind == -1 or problem_spec_end_ind == -1 \
            or implementation_signature_start_ind == -1 or implementation_signature_end_ind == -1 \
            or test_cases_start_ind == -1 or test_cases_end_ind == -1 \
            or correctness_definition_start_ind == -1 or correctness_definition_end_ind == -1:
        raise ValueError(f"Problem file has wrong format.")

    problem_statement_start_ind += len(PROBLEM_STATEMENT_START_STRING)
    problem_spec_start_ind += len(PROBLEM_SPEC_START_STRING)
    implementation_signature_start_ind += len(IMPLEMENTATION_SIGNATURE_START_STRING)
    test_cases_start_ind += len(TEST_CASES_START_STRING)
    correctness_definition_start_ind += len(CORRECTNESS_DEFINITION_START_STRING)

    problem_statement = raw_problem[problem_statement_start_ind:problem_statement_end_ind].strip()
    problem_spec = raw_problem[problem_spec_start_ind:problem_spec_end_ind].strip()
    implementation_signature = raw_problem[implementation_signature_start_ind:implementation_signature_end_ind].strip()
    test_cases = raw_problem[test_cases_start_ind:test_cases_end_ind].strip()
    correctness_definition = raw_problem[correctness_definition_start_ind:correctness_definition_end_ind].strip()

    implementation_signature += "\nsorry"
    correctness_definition += " by\nsorry"

    return problem_statement, problem_spec, implementation_signature, test_cases, correctness_definition
