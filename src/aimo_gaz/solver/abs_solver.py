from abc import ABC, abstractmethod

class Solver(ABC):

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def solve(self, problem_description: str) -> int:
        pass

    @abstractmethod
    def solve_intermediate(self, problem_description: str) -> str:
        pass