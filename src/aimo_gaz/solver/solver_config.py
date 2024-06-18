import omegaconf
import os
from aimo_gaz.prompts.prompt import Prompt, ConcatPrompt
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from enum import Enum
from aimo_gaz.solver.test_solver import TestSolver
from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.solver.vanilla_few_shot_solver import FewShotSolver as VanilaFewShotSolver
from aimo_gaz.models.model import Model

class PromptType(Enum):
    Concat = "Concat"

    def __str__(self):
        return self.value

class SolverType(Enum):
    TestSolver = "TestSolver"
    VanillaFewShotSolver = "VanillaFewShotSolver"

    def __str__(self):
        return self.value

@dataclass_json
@dataclass
class PromptConfig:
    prompt_type: PromptType
    system_prompt_path: str
    example_prompt_path: str
    
    def get_prompt(self) -> Prompt:
        if self.prompt_type == PromptType.Concat:
            return ConcatPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        else:
            raise NotImplementedError(f"Prompt type {self.prompt_type} is not implemented.")

@dataclass_json
@dataclass
class ModelSettings(object):
    name_or_path: str
    logging_dir: str
    model_args: dict = field(default_factory=dict)


@dataclass_json
@dataclass
class InferenceSettings:
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    do_sample: bool
    num_return_sequences: int
    max_length: int
    stop_tokens: list = field(default_factory=list)

@dataclass_json
@dataclass
class SolverConfig:
    model_settings: ModelSettings
    inference_settings: InferenceSettings
    prompt_config: PromptConfig
    solver_type: SolverType
    solver_args: dict = field(default_factory=dict)

    def get_solver(self) -> Solver:
        if self.solver_type == SolverType.TestSolver:
            return TestSolver()
        elif self.solver_type == SolverType.VanillaFewShotSolver:
            model = Model(self.model_settings.name_or_path, self.model_settings.logging_dir, **self.model_settings.model_args)
            prompt = self.prompt_config.get_prompt()
            inference_settings_dict = self.inference_settings.to_dict()
            return VanilaFewShotSolver(model, prompt, **inference_settings_dict)
        else:
            raise NotImplementedError(f"Solver type {self.solver_type} is not implemented.")

def recursive_replace_keywords(cfg, key_word: str, replace_word: str):
    if isinstance(cfg, omegaconf.dictconfig.DictConfig) or isinstance(cfg, dict):
        keys = [key for key in cfg] # to avoid immutable dict error
        for key in keys:
            value = cfg[key]
            if isinstance(value, str):
                cfg[key] = value.replace(key_word, replace_word)
            elif isinstance(value, omegaconf.dictconfig.DictConfig) or \
                isinstance(value, omegaconf.listconfig.ListConfig) or \
                isinstance(value, dict) or \
                isinstance(value, list):
                recursive_replace_keywords(value, key_word, replace_word)
    elif isinstance(cfg, omegaconf.listconfig.ListConfig) or isinstance(cfg, list):
        for i in range(len(cfg)):
            value = cfg[i]
            if isinstance(value, str):
                cfg[i] = value.replace(key_word, replace_word)
            elif isinstance(value, omegaconf.dictconfig.DictConfig) or \
                isinstance(value, omegaconf.listconfig.ListConfig) or \
                isinstance(value, dict) or \
                isinstance(value, list):
                recursive_replace_keywords(value, key_word, replace_word)
    else:
        raise Exception(f"Invalid type: {type(cfg)}")

def parse_solver_config(cfg) -> SolverConfig:
    if "AIMO_GAZ_ROOT" in os.environ:
        gaz_root = os.environ["AIMO_GAZ_ROOT"]
    else:
        gaz_root = None
    if gaz_root is not None:
        # Replace all the <gaz_root> placeholders in all the paths in all the setting
        recursive_replace_keywords(cfg, "<AIMO_GAZ_ROOT>", gaz_root)
    inference_settings = InferenceSettings(**cfg["inference_settings"])
    model_settings = ModelSettings(**cfg["model_settings"])
    prompt_config = PromptConfig(**cfg["prompt_config"])
    prompt_config.prompt_type = PromptType(cfg["prompt_config"]["prompt_type"])
    solver_config = SolverConfig(
        model_settings=model_settings, 
        inference_settings=inference_settings, 
        prompt_config=prompt_config, 
        solver_type=SolverType(cfg["solver_type"]),
        solver_args=cfg["solver_args"])
    return solver_config
