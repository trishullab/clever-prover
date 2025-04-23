import typing
from enum import Enum
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_prover.baselines.few_shot_spec_generation import FewShotSpecGenerationTask
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

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

class ImplementationGenerationStrategy(Enum):
    FewShotImplGeneration = "FewShotImplGeneration"

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
        raise NotImplementedError("FewShotImplGeneration is not implemented yet")
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def parse_spec_generation_class(cfg) -> typing.Type[SpecGenerationTask]:
    task_type = TaskType(cfg["task_type"])
    assert task_type == TaskType.SPEC_ISOMORPHISM, "Only SPEC_ISOMORPHISM can be used for spec generation"
    spec_generation_strategy = SpecGenerationStrategy(cfg["spec_generation_strategy"])
    if spec_generation_strategy == SpecGenerationStrategy.FewShotSpecGeneration:
        return FewShotSpecGenerationTask
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def parse_spec_isomorphism_config(cfg):
    spec_prompt_settings = PromptSettings.from_dict(cfg["spec_prompt_settings"])
    spec_model_settings = ModelSettings.from_dict(cfg["spec_model_settings"])
    proof_prompt_settings = PromptSettings.from_dict(cfg["proof_prompt_settings"])
    proof_model_settings = ModelSettings.from_dict(cfg["proof_model_settings"])
    return {
        "spec_prompt_settings": spec_prompt_settings,
        "spec_model_settings": spec_model_settings,
        "proof_prompt_settings": proof_prompt_settings,
        "proof_model_settings": proof_model_settings,
        "lemma_name": cfg["lemma_name"] if "lemma_name" in cfg else "spec_isomorphism"
    }

def parse_impl_correctness_config(cfg):
    impl_prompt_settings = PromptSettings.from_dict(cfg["impl_prompt_settings"])
    impl_model_settings = ModelSettings.from_dict(cfg["impl_model_settings"])
    proof_prompt_settings = PromptSettings.from_dict(cfg["proof_prompt_settings"])
    proof_model_settings = ModelSettings.from_dict(cfg["proof_model_settings"])
    return {
        "impl_prompt_settings": impl_prompt_settings,
        "impl_model_settings": impl_model_settings,
        "proof_prompt_settings": proof_prompt_settings,
        "proof_model_settings": proof_model_settings,
        "lemma_name": cfg["lemma_name"] if "lemma_name" in cfg else "impl_correctness"
    }