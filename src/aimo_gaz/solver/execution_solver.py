from aimo_gaz.solver.abs_solver import Solver
import logging
import os
import tempfile
from subprocess import Popen, PIPE, STDOUT

class ExecutionSolver(Solver):
    def __init__(self, timeout_in_secs: int, logger: logging.Logger = None, **inference_kwargs):
        assert logger is not None, "logger must be provided."
        self.logger = logger
        self.inference_kwargs = inference_kwargs
        self.history = []
        self.timeout_in_secs = timeout_in_secs
    
    def run(self, filepath: str, timeout_in_secs: float = 120.0):
        assert os.path.isfile(filepath), f"filepath must be a valid file: {filepath}"
        process = Popen(
            ['python', filepath], 
            stdin = PIPE, 
            stdout = PIPE, 
            stderr = STDOUT,
            bufsize = 1, 
            universal_newlines = True)
        # Start the process, and wait for it to finish
        process.wait(timeout=timeout_in_secs)
        is_timeout = process.poll() is None
        # Get the output
        output = process.stdout.read()
        # Kill the process if it is still running
        process.kill()
        # Return the output
        return self.parse_output(is_timeout, process, output)
    
    def parse_output(self, is_timeout, process: Popen, output: str) -> str:
        if is_timeout:
            return f"""
[OUTPUT START]
Execution timed out after {self.timeout_in_secs} seconds.
[TIMEOUT]
[OUTPUT END]
"""
        else:
            return output

    def solve(self, problem_description: str) -> int:
        raise NotImplementedError("This method is not implemented.")
    
    def code_decorator(self, code: str) -> str:
        code = code.replace('\n', '\n    ') # Add indentation to put the code in a try-except block
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
print("[OUTPUT END]")
"""
        return new_code

    def solve_intermediate(self, problem_description: str) -> str:
        code = problem_description
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
            self.logger.info(f"Output:\n{output}")
        self.history.append({"role": "assistant", "content": output})
        return output
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

if __name__ == "__main__":
    # Test the ExecutionSolver class
    import time
    from aimo_gaz.tools.log_utils import setup_logger
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    os.makedirs(f".logs/{time_str}/temp", exist_ok=True)
    logger = setup_logger("aimo_gaz", f".logs/{time_str}/execution_solver_test.log")
    code = """
x = symbols('x')
eq = Eq(x**2 - 2*x - 8, 0)
print(f\"Solving equation: {eq}\")
sol = solve(eq, x)
print(sol)
"""
    solver = ExecutionSolver(timeout_in_secs=10, logger=logger)
    with solver:
        output = solver.solve_intermediate(code)
        print(output)