import typing
from enum import Enum
from clever_prover.utils.configs import PromptSettings, ModelSettings
from clever_prover.baselines.few_shot_spec_generation import FewShotSpecGenerationTask, SpecGenerationTask

class TaskType(Enum):
    SPEC_ISOMORPHISM = "SPEC_ISOMORPHISM"

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

def parse_config(cfg):
    task_type = TaskType(cfg["task_type"])
    if task_type == TaskType.SPEC_ISOMORPHISM:
        return parse_spec_isomorphism_config(cfg)
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