import ray
import ray.actor
import os
from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from clever_prover.main.parse_config import TaskType


@dataclass_json
@dataclass
class ExecutionInfo:
    """
    ExecutionInfo is a dataclass that contains information about the execution of a task.
    It is used to store the task ID, the start time, and the end time of the task.
    """
    problem_id: int
    attempt_count: int
    task_type: TaskType
    generation_time: float
    proof_time: float
    total_time: float
    compiles: bool
    is_proven: bool

    def __str__(self):
        return self.to_json()

@ray.remote
class Checkpoint:
    def __init__(self, execution_info: Optional[list[ExecutionInfo]] = None):
        self.execution_info = execution_info if execution_info else []

    def add_execution_info(self, info: ExecutionInfo):
        if info.is_proven:
            assert info.compiles, "If the problem is proven, it should also be compilable."
        self.execution_info.append(info)

    def get_execution_info(self) -> list[ExecutionInfo]:
        return self.execution_info

    def save_checkpoint(self, file_path: str):
        with open(file_path, 'w') as f:
            for info in self.execution_info:
                f.write(info.to_json() + '\n')

class CheckpointWrapper:
    def __init__(self, actor: ray.actor.ActorHandle, save_path: str):
        self.actor = actor
        self.save_path = save_path

    @classmethod
    def new(cls, save_path: str) -> "CheckpointWrapper":
        actor = Checkpoint.remote()
        return cls(actor, save_path)

    @classmethod
    def from_file(cls, file_path: str) -> "CheckpointWrapper":
        execution_info = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    execution_info.append(ExecutionInfo.from_json(line))
        # If file doesn't exist, initialize with empty list
        actor = Checkpoint.remote(execution_info=execution_info)
        return cls(actor, file_path)

    def add(self, info: ExecutionInfo):
        if info.is_proven:
            assert info.compiles, "If the problem is proven, it should also be compilable."
        add_remote = self.actor.add_execution_info.remote(info)
        ray.get(add_remote)

    def get_all(self) -> list[ExecutionInfo]:
        execution_info_remote = self.actor.get_execution_info.remote()
        execution_info = ray.get(execution_info_remote)
        return execution_info

    def save(self):
        save_checkpoint_remote = self.actor.save_checkpoint.remote(self.save_path)
        ray.get(save_checkpoint_remote)
    
    def is_attempted_k_times(self, problem_id: int, k: int) -> bool:
        execution_info = self.get_all()
        return any(info.problem_id == problem_id and info.attempt_count >= k for info in execution_info)
    
    def get_all_attempts(self, problem_id: int) -> list[ExecutionInfo]:
        execution_info = self.get_all()
        return [info for info in execution_info if info.problem_id == problem_id]
    
    def was_solved(self, problem_id: int) -> bool:
        execution_info = self.get_all()
        return any(info.problem_id == problem_id and info.is_proven for info in execution_info)
    
    def was_compiled(self, problem_id: int) -> bool:
        execution_info = self.get_all()
        return any(info.problem_id == problem_id and info.compiles for info in execution_info)