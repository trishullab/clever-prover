from abc import ABC, abstractmethod

class Solver(ABC):
    @abstractmethod
    def solve(self, problem_description: str):
        pass