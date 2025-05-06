import typing
from enum import Enum
from omegaconf.dictconfig import DictConfig
from omegaconf.listconfig import ListConfig
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_prover.baselines.few_shot_spec_generation import FewShotSpecGenerationTask
from clever_prover.baselines.few_shot_implementation_generation import FewShotImplementationGenerationTask
from clever_prover.solver.impl_generator import ImplGenerator
from clever_prover.solver.iso_generator import IsoGenerator
from clever_prover.tasks.spec_generation_task import SpecGenerationTask
from clever_prover.tasks.implementation_generation_task import ImplementationGenerationTask

class TaskType(Enum):
    SPEC_ISOMORPHISM = "SPEC_ISOMORPHISM"
    IMPL_CORRECTNESS = "IMPL_CORRECTNESS"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
    
class SpecGenerationStrategy(Enum):
    FewShotSpecGeneration = "FewShotSpecGeneration"
    IsoGenerator = "IsoGenerator"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

class ImplementationGenerationStrategy(Enum):
    FewShotImplGeneration = "FewShotImplGeneration"
    ImplGenerator = "ImplGenerator"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

def parse_config(cfg):
    task_type = TaskType(cfg["task_type"])
    if task_type == TaskType.SPEC_ISOMORPHISM:
        return parse_spec_isomorphism_config(cfg)
    elif task_type == TaskType.IMPL_CORRECTNESS:
        return parse_impl_correctness_config(cfg)
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def parse_impl_generation_class(cfg) -> typing.Type[ImplementationGenerationTask]:
    task_type = TaskType(cfg["task_type"])
    assert task_type == TaskType.IMPL_CORRECTNESS, "Only IMPL_CORRECTNESS can be used for implementation generation"
    impl_generation_strategy = ImplementationGenerationStrategy(cfg["impl_generation_strategy"])
    if impl_generation_strategy == ImplementationGenerationStrategy.FewShotImplGeneration:
        return FewShotImplementationGenerationTask
    elif impl_generation_strategy == ImplementationGenerationStrategy.ImplGenerator:
        return ImplGenerator
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def parse_spec_generation_class(cfg) -> typing.Type[SpecGenerationTask]:
    task_type = TaskType(cfg["task_type"])
    assert task_type == TaskType.SPEC_ISOMORPHISM, "Only SPEC_ISOMORPHISM can be used for spec generation"
    spec_generation_strategy = SpecGenerationStrategy(cfg["spec_generation_strategy"])
    if spec_generation_strategy == SpecGenerationStrategy.FewShotSpecGeneration:
        return FewShotSpecGenerationTask
    elif spec_generation_strategy == SpecGenerationStrategy.IsoGenerator:
        return IsoGenerator
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def parse_spec_isomorphism_config(cfg):
    params = cfg["params"]
    params_dict = {}
    for key, value in params.items():
        if isinstance(value, DictConfig):
            if "prompt_settings" in key:
                value : PromptSettings = PromptSettings.from_dict(value)
                params_dict[key] = value
            elif "model_settings" in key:
                params_dict[key] = ModelSettings.from_dict(value)
            else:
                raise ValueError(f"Unknown parameter type for key: {key}")
        elif isinstance(value, ListConfig):
            # Convert ListConfig to a regular list
            params_dict[key] = [item for item in value]
        else:
            params_dict[key] = value
    return params_dict

def parse_impl_correctness_config(cfg):
    params = cfg["params"]
    params_dict = {}
    for key, value in params.items():
        if isinstance(value, DictConfig):
            if "prompt_settings" in key:
                value : PromptSettings = PromptSettings.from_dict(value)
                params_dict[key] = value
            elif "model_settings" in key:
                params_dict[key] = ModelSettings.from_dict(value)
            else:
                raise ValueError(f"Unknown parameter type for key: {key}")
        elif isinstance(value, ListConfig):
            params_dict[key] = [item for item in value]
        else:
            params_dict[key] = value
    return params_dict