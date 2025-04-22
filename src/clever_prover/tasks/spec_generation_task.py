import logging
import uuid
import time
import os
from clever_bench.task import ProblemViewTask
from abc import ABC, abstractmethod

class SpecGenerationTask(ABC):
    """
    Abstract base class for specification generation tasks.
    """

    def __init__(self,    
        problem_id: int,
        problem_view: ProblemViewTask, 
        lemma_name="spec_isomorphism"):
        assert isinstance(problem_id, int), "problem_id should be an integer"
        assert problem_id >= 0, "problem_id should be a non-negative integer"
        assert isinstance(problem_view, ProblemViewTask), "problem_view should be an instance of ProblemViewTask"
        project_path = problem_view.benchmark.project_path
        time_tick = time.time()
        temp_file_name = f"temptodel{uuid.uuid4()}{time_tick}.lean"
        file_path = os.path.join(project_path, temp_file_name)
        self.problem_view = problem_view
        self.problem_id = problem_id
        self.project_path = project_path
        self.file_path = file_path
        self.lemma_name = lemma_name

    @abstractmethod
    def generate_specification(self, timeout_in_ms: float = 60, logger: logging.Logger = None) -> str:
        """
        Generate a specification for the task.
        """
        pass

    @abstractmethod
    def generate_spec_isomorphism_proof(self, timeout_in_ms: float = 60, logger: logging.Logger = None) -> str:
        """
        Validate the generated specification.
        """
        pass