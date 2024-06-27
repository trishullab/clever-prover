from aimo_gaz.solver.abs_solver import Solver

class TestSolver(Solver):
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def solve(self, problem_description: str):
        return 1
    
    def solve_intermediate(self, problem_description: str,  time_allowed: int):
        return "1"
    
    def reset(self):
        pass