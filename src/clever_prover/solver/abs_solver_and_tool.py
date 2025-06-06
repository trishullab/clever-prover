from abc import ABC, abstractmethod

class Solver(ABC):

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def solve(self, problem_statement: str, time_allowed: int) -> float:
        pass

    @abstractmethod
    def reset(self):
        pass

class Tool(ABC):

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def solve_intermediate(self, problem_statement: str):
        pass

    @abstractmethod
    def reset(self):
        pass
