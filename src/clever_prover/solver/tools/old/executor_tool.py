from clever_prover.solver.abs_solver_and_tool import Tool
import logging
import os
import tempfile
import typing
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

class ExecutorTool(Tool):
    def __init__(self, logger: logging.Logger = None, timeout_in_secs: float = 10.0):
        assert logger is not None, "Logger must be provided."
        self.logger = logger
        self.timeout_in_secs = timeout_in_secs
        self.history = []
    
    def run(self, filepath: str, timeout_in_secs: float = 10.0):
        assert os.path.isfile(filepath), f"Filepath must be a valid file: {filepath}"
        process = Popen(
            ['python', filepath],
            stdin = PIPE,
            stdout = PIPE,
            stderr = STDOUT,
            bufsize = 1,
            universal_newlines = True)
        # Start the process, and wait for it to finish
        output = None
        try:
            output, _ = process.communicate(timeout=timeout_in_secs)
            is_timeout = False
        except TimeoutExpired:
            is_timeout = True
        # Kill the process if it is still running
        process.kill()
        # Return the output
        return self.parse_output(is_timeout, process, output)
    
    def run_parallel(self, filepaths: list, timeout_in_secs: float = 10.0) -> typing.List[str]:
        assert len(filepaths) > 0, "Filepaths must not be empty."
        processes : typing.List[Popen] = []
        outputs = []
        for filepath in filepaths:
            assert os.path.isfile(filepath), f"Filepath must be a valid file: {filepath}"
            process = Popen(
                ['python', filepath],
                stdin = PIPE,
                stdout = PIPE,
                stderr = STDOUT,
                bufsize = 1,
                universal_newlines = True)
            processes.append(process)
        for process in processes:
            # Start the process, and wait for it to finish
            # This won't really be sequential because other processes are running in background
            output = None
            try:
                output, _ = process.communicate(timeout=timeout_in_secs)
                is_timeout = False
            except TimeoutExpired:
                is_timeout = True
            if is_timeout:
                # One worst case when every process times out, this will block sequentially waiting for each process
                # So if one process timeout, probably other either finished or are about to finish or timed out
                # So we reduce the timeout to 1 second because other processes should have finished by now
                timeout_in_secs = 1
            # Kill the process if it is still running
            process.kill()
            # Return the output
            outputs.append(self.parse_output(is_timeout, process, output))
        return outputs
    
    def parse_output(self, is_timeout, process: Popen, output: str) -> str:
        if is_timeout:
            return f"""
[OUTPUT START]
Execution timed out after {self.timeout_in_secs} seconds.
[TIMEOUT]
[OUTPUT END]"""
        elif process.returncode != 0 and not output.endswith("[OUTPUT END]"):
            return f"""
[OUTPUT START]
Execution failed with return code {process.returncode}.
{output}
[CODE RAISED EXCEPTION]
[OUTPUT END]"""
        else:
            return output
    
    def code_decorator(self, code: str) -> str:
        code = code.lstrip() # Remove leading whitespace
        # Add indentation to put the code in a try-except block
        code = "    " + code.replace('\n', '\n    ')
        # code = code.replace('\n', '\n    ') # Add indentation to put the code in a try-except block
        new_code = f"""
print("[OUTPUT START]")
try:
    from sympy import *
    import sympy
    import numpy as np
except:
    print("Could not import sympy or numpy.")

try:
{code}
    print("[CODE RAN SUCCESSFULLY]")
except Exception as e:
    print(e)
    print("[CODE RAISED EXCEPTION]")
print("[OUTPUT END]")"""
        return new_code

    def solve_intermediate(self, problem_statement: str) -> str:
        code = problem_statement
        message = {"role": "user", "content": code}
        self.history.append(message)
        code = self.code_decorator(code)
        # Save the code to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w') as f:
            self.logger.info(f"Writing code to file: {f.name}")
            self.logger.info(f"Code:\n{code}")
            f.write(code)
            f.flush()
            fullpath = f.name
            # Run the code
            output = self.run(fullpath, self.timeout_in_secs)
            output = output.strip()
            self.logger.info(f"Output:\n{output}")
        self.history.append({"role": "assistant", "content": output})
        return output
    
    def solve_intermediate_parallel(self, problem_statements: typing.List[str]) -> typing.List[str]:
        codes = problem_statements
        tempfiles = []
        for i, code in enumerate(codes):
            try:
                code = self.code_decorator(code)
                with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
                    self.logger.info(f"Writing code to file: {f.name}")
                    self.logger.info(f"Code {i}:\n{code}")
                    f.write(code)
                    f.flush()
                    fullpath = f.name
                    tempfiles.append(fullpath)
            except Exception as e:
                self.logger.warn(f"Exception when writing code: {e}")
        # Run the code in parallel
        outputs = self.run_parallel(tempfiles, self.timeout_in_secs)
        for i, output in enumerate(outputs):
            output = output.strip()
            self.logger.info(f"Output {i}:\n{output}")
            # Remove the temporary file
            os.remove(tempfiles[i])
        return outputs
    
    def extract_last_output(self, output: str) -> typing.Tuple[str, bool]:
        # Find the last occurence of "[OUTPUT END]"
        output = output.strip()
        assert output.endswith("[OUTPUT END]"), "Output does not end with [OUTPUT END]"
        stripped_output = output[:-len("[OUTPUT END]")].strip()
        code_success = False
        if stripped_output.endswith("[CODE RAN SUCCESSFULLY]"):
            stripped_output = stripped_output[:-len("[CODE RAN SUCCESSFULLY]")].strip()
            code_success = True
        elif stripped_output.endswith("[CODE RAISED EXCEPTION]"):
            stripped_output = stripped_output[:-len("[CODE RAISED EXCEPTION]")].strip()
        elif stripped_output.endswith("[TIMEOUT]"):
            stripped_output = stripped_output[:-len("[TIMEOUT]")].strip()
        # Find the last newline character
        last_newline_index = stripped_output.rfind('\n')
        if last_newline_index == -1:
            last_output = stripped_output[len("[OUTPUT START]"):].strip()
        else:
            last_output = stripped_output[last_newline_index:].strip()
        return last_output, code_success
    
    def reset(self):
        self.history = []

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

if __name__ == "__main__":
    # Test the ExecutorTool class
    import time
    from clever_prover.utils.log_utils import setup_logger
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    os.makedirs(f".logs/{time_str}/temp", exist_ok=True)
    logger = setup_logger("clever_prover", f".logs/{time_str}/executor_tool_test.log")
    code = """
x = symbols('x')
eq = Eq(x**2 - 2*x - 8, 0)
print(f\"Solving equation: {eq}\")
sol = solve(eq, x)
print(sol)
"""
    tool = ExecutorTool(logger=logger, timeout_in_secs=5)
    with tool:
        output = tool.solve_intermediate(code)
        print(output)
