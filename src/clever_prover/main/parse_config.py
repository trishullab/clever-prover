from enum import Enum
from clever_prover.utils.configs import PromptSettings, ModelSettings

class TaskType(Enum):
    SPEC_ISOMORPHISM = "SPEC_ISOMORPHISM"

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
        "proof_dump_file_name": cfg["proof_dump_file_name"],
        "lemma_name": cfg["lemma_name"] if "lemma_name" in cfg else "spec_isomorphism"
    }