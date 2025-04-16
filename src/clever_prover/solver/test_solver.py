from clever_prover.solver.abs_solver_and_tool import Solver

class TestSolver(Solver):
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def solve(self, problem_statement: str):
        return 1
    
    def reset(self):
        pass
