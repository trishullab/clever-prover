import omegaconf
import os
import logging
import typing
import hydra
from aimo_gaz.prompts.prompt import Prompt, ConcatPrompt
from aimo_gaz.prompts.cot_prompt import CoTPrompt
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from enum import Enum
from aimo_gaz.models.abs_model import Model
from aimo_gaz.models.gpt_model import GptModel
if os.environ.get("USE_VLLM", "False").lower() == "true":
    # In case we cannot install VLLM
    from vllm import LLM, SamplingParams


class vLLMHarness(Model):
    def __init__(self, model, sampling_params):
        self.model = model
        self.sampling_params = sampling_params
    
    def is_loaded(self):
        return True

    def generate(self, prompt, **kwargs):
        # TODO: - yucky, not sure if they have a standard way of doing this.
        kwargs = self.make_safe_sampling_params(kwargs, self.model)
        for key, value in kwargs.items():
            setattr(self.sampling_params, key, value)
        out = self.model.generate(prompt, self.sampling_params)
        return out

    def parse_out(self, out):
        generated_text = [[y.text for y in x.outputs] for x in out]
        return generated_text


    @classmethod
    def make_safe_sampling_params(cls, sampling_params, model):
        safe_sampling_params = {}
        for k, v in sampling_params.items():
            if k == 'max_new_tokens':
                safe_sampling_params['max_tokens'] = v
            elif k in ['temperature', 'top_p', 'top_k']:
                if v is not None:
                    safe_sampling_params[k] = v
            elif k == 'num_return_sequences':
                safe_sampling_params['n'] = v
            elif k == 'stop_tokens':
                safe_sampling_params['stop'] = v#[model.get_tokenizer().convert_tokens_to_ids(x) for x in v if model.get_tokenizer().convert_tokens_to_ids(x) is not None]
            else:
                continue

        return safe_sampling_params

    @classmethod
    def load_from_config(cls, model_name, vllm_params, sampling_params):
        model = LLM(model_name, **vllm_params)
        sampling_params = SamplingParams(**cls.make_safe_sampling_params(sampling_params, model))
        return cls(model, sampling_params)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


from aimo_gaz.solver.test_solver import TestSolver
from aimo_gaz.solver.abs_solver_and_tool import Solver, Tool
from aimo_gaz.solver.vanilla_few_shot_solver import FewShotSolver as VanillaFewShotSolver
from aimo_gaz.solver.coordination_solver import CoordinationSolver, CoordinationSolverStrategy
from aimo_gaz.solver.tools.old_code_tool import OldCodeTool
from aimo_gaz.solver.tools.old_planner_tool import OldPlannerTool
from aimo_gaz.solver.tools.execution_tool import ExecutionTool
from aimo_gaz.solver.tools.coordinator_tool import CoordinatorTool
from aimo_gaz.solver.tools.planner_tool import PlannerTool
from aimo_gaz.solver.tools.llm_guesser_tool import LLMGuesserTool
from aimo_gaz.models.gpt_model import GptModel
from aimo_gaz.prompts.old_code_prompt import OldCodePrompt
from aimo_gaz.prompts.old_planner_prompt import OldPlannerPrompt
from aimo_gaz.prompts.coordinator_prompt import CoordinatorPrompt
from aimo_gaz.prompts.planner_prompt import PlannerPrompt
from aimo_gaz.prompts.llm_guesser_prompt import LLMGuesserPrompt

GLOBAL_MODEL_CACHE = {}

class PromptType(Enum):
    Concat = "Concat"
    CoTPrompt = "CoTPrompt"
    OldCodePrompt = "OldCodePrompt"
    OldPlannerPrompt = "OldPlannerPrompt"
    CoordinatorPrompt = "CoordinatorPrompt"
    PlannerPrompt = "PlannerPrompt"
    LLMGuesserPrompt = "LLMGuesserPrompt"

    def __str__(self):
        return self.value

class SolverOrToolType(Enum):
    TestSolver = "TestSolver"
    VanillaFewShotSolver = "VanillaFewShotSolver"
    CoordinationSolver = "CoordinationSolver"
    OldCodeTool = "OldCodeTool"
    OldPlannerTool = "OldPlannerTool"
    ExecutionTool = "ExecutionTool"
    CoordinatorTool = "CoordinatorTool"
    PlannerTool = "PlannerTool"
    LLMGuesserTool = "LLMGuesserTool"

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
        elif self.prompt_type == PromptType.CoTPrompt:
            return CoTPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        elif self.prompt_type == PromptType.OldCodePrompt:
            return OldCodePrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        elif self.prompt_type == PromptType.OldPlannerPrompt:
            return OldPlannerPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        elif self.prompt_type == PromptType.CoordinatorPrompt:
            return CoordinatorPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        elif self.prompt_type == PromptType.PlannerPrompt:
            return PlannerPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        elif self.prompt_type == PromptType.LLMGuesserPrompt:
            return LLMGuesserPrompt(system_prompt_path=self.system_prompt_path, example_prompt_path=self.example_prompt_path)
        else:
            raise NotImplementedError(f"Prompt type {self.prompt_type} is not implemented.")

@dataclass_json
@dataclass
class ModelSettings(object):
    name_or_path: str
    logging_dir: str
    use_vllm: bool
    model_args: dict = field(default_factory=dict)
    vllm_model_args: dict = field(default_factory=dict)
    vllm_sample_args: dict = field(default_factory=dict)

# @dataclass_json
# @dataclass
# class InferenceSettings:
#     max_new_tokens: int
#     temperature: float
#     top_p: float
#     top_k: int
#     do_sample: bool
#     num_return_sequences: int
#     max_length: int
#     return_full_text: bool
#     stop_tokens: list = field(default_factory=list)

@dataclass_json
@dataclass
class InferenceSettings:
    max_tokens: int
    temperature: float
    top_p: float
    n: int
    stop: list = field(default_factory=list)


@dataclass_json
@dataclass
class SolverOrToolConfig:
    model_settings: ModelSettings
    inference_settings: InferenceSettings
    prompt_config: PromptConfig
    solver_or_tool_type: SolverOrToolType
    solver_or_tool_args: dict = field(default_factory=dict)

    def get_solver_or_tool(self, logger: logging.Logger) -> typing.Union[Solver, Tool]:
        if self.solver_or_tool_type == SolverOrToolType.TestSolver:
            return TestSolver()
        elif self.solver_or_tool_type == SolverOrToolType.VanillaFewShotSolver:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                if self.model_settings.use_vllm:
                    vllm_model = LLM(self.model_settings.name_or_path, **self.model_settings.vllm_model_args)
                    sampling_params = SamplingParams(**self.model_settings.vllm_sample_args)
                    model = vLLMHarness(vllm_model, sampling_params)
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model

                else:
                    model = GptModel(self.model_settings.name_or_path, self.model_settings.logging_dir,
                                  **self.model_settings.model_args)
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]

            prompt = self.prompt_config.get_prompt()
            inference_settings_dict = self.inference_settings.to_dict()
            return VanillaFewShotSolver(model, prompt, logger, **inference_settings_dict)
        elif self.solver_or_tool_type == SolverOrToolType.OldCodeTool:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                if self.model_settings.use_vllm:
                    vllm_model = LLM(self.model_settings.name_or_path, **self.model_settings.vllm_model_args)
                    sampling_params = SamplingParams(**self.model_settings.vllm_sample_args)
                    model = vLLMHarness(vllm_model, sampling_params)
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model

                else:
                    model = GptModel(self.model_settings.name_or_path,
                                    #  self.model_settings.logging_dir,
                                    #  **self.model_settings.model_args,
                                    )
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]
            prompt = self.prompt_config.get_prompt()
            return OldCodeTool(model, prompt, logger, **self.inference_settings.to_dict())
        elif self.solver_or_tool_type == SolverOrToolType.OldPlannerTool:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                if self.model_settings.use_vllm:
                    vllm_model = LLM(self.model_settings.name_or_path, **self.model_settings.vllm_model_args)
                    sampling_params = SamplingParams(**self.model_settings.vllm_sample_args)
                    model = vLLMHarness(vllm_model, sampling_params)
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model

                else:
                    model = GptModel(self.model_settings.name_or_path,
                                    #  self.model_settings.logging_dir,
                                    #  **self.model_settings.model_args,
                                    )
                    GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]
            prompt = self.prompt_config.get_prompt()
            return OldPlannerTool(model, prompt, logger, **self.inference_settings.to_dict())
        elif self.solver_or_tool_type == SolverOrToolType.ExecutionTool:
            return ExecutionTool(logger, **self.solver_or_tool_args)
        elif self.solver_or_tool_type == SolverOrToolType.CoordinatorTool:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                model = GptModel(self.model_settings.name_or_path)
                GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]
            prompt = self.prompt_config.get_prompt()
            return CoordinatorTool(model, prompt, logger, **self.inference_settings.to_dict())
        elif self.solver_or_tool_type == SolverOrToolType.PlannerTool:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                model = GptModel(self.model_settings.name_or_path)
                GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]
            prompt = self.prompt_config.get_prompt()
            return PlannerTool(model, prompt, logger, **self.inference_settings.to_dict())
        elif self.solver_or_tool_type == SolverOrToolType.LLMGuesserTool:
            if self.model_settings.name_or_path not in GLOBAL_MODEL_CACHE:
                model = GptModel(self.model_settings.name_or_path)
                GLOBAL_MODEL_CACHE[self.model_settings.name_or_path] = model
            else:
                model = GLOBAL_MODEL_CACHE[self.model_settings.name_or_path]
            prompt = self.prompt_config.get_prompt()
            return LLMGuesserTool(model, prompt, logger, **self.inference_settings.to_dict())
        else:
            raise NotImplementedError(f"Solver type {self.solver_or_tool_type} is not implemented.")

@dataclass_json
@dataclass
class CoordinationSolverConfig:
    # planner: SolverOrToolConfig
    # executor: SolverOrToolConfig
    # coder: SolverOrToolConfig
    tool_configs: typing.Dict[str, SolverOrToolConfig]
    strategy: CoordinationSolverStrategy
    coordination_kwargs: dict = field(default_factory=dict)

    def get_solver_or_tool(self, logger: logging.Logger) -> CoordinationSolver:
        # tools = {
        #     "planner": self.planner.get_solver_or_tool(logger),
        #     "executor": self.executor.get_solver_or_tool(logger),
        #     "coder": self.coder.get_solver_or_tool(logger),
        # }
        tools = {}
        for tool_name, tool_config in self.tool_configs.items():
            tools[tool_name] = tool_config.get_solver_or_tool(logger)
        return CoordinationSolver(tools, self.strategy, logger, **self.coordination_kwargs)


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

def parse_solver_or_tool_config(cfg) -> typing.Union[SolverOrToolConfig, CoordinationSolverConfig]:
    if "AIMO_GAZ_ROOT" in os.environ:
        gaz_root = os.environ["AIMO_GAZ_ROOT"]
    else:
        gaz_root = None
    if gaz_root is not None:
        # Replace all the <gaz_root> placeholders in all the paths in all the setting
        recursive_replace_keywords(cfg, "<AIMO_GAZ_ROOT>", gaz_root)
    is_coordination_solver = "tools" in cfg
    if not is_coordination_solver:

        model_settings = ModelSettings(**cfg["model_settings"])
        inference_settings = InferenceSettings(**cfg["inference_settings"])

        prompt_config = PromptConfig(**cfg["prompt_config"])
        prompt_config.prompt_type = PromptType(cfg["prompt_config"]["prompt_type"])
        solver_or_tool_config = SolverOrToolConfig(
            model_settings=model_settings,
            inference_settings=inference_settings,
            prompt_config=prompt_config,
            solver_or_tool_type=SolverOrToolType(cfg["solver_or_tool_type"]),
            solver_or_tool_args=cfg["solver_or_tool_args"])
        return solver_or_tool_config
    else:
        strategy = CoordinationSolverStrategy(cfg["strategy"])
        coordination_kwargs = cfg["coordination_kwargs"]
        # planner_config = cfg["tools"]["planner"]
        # executor_config = cfg["tools"]["executor"]
        # coder_config = cfg["tools"]["coder"]
        # planner_cfg = hydra.compose(config_name=planner_config)
        # executor_cfg = hydra.compose(config_name=executor_config)
        # coder_cfg = hydra.compose(config_name=coder_config)
        # planner = parse_solver_or_tool_config(planner_cfg)
        # executor = parse_solver_or_tool_config(executor_cfg)
        # coder = parse_solver_or_tool_config(coder_cfg)
        tool_configs = {}
        for tool_name, tool_config in cfg["tools"].items():
            tool_cfg = hydra.compose(config_name=tool_config)
            tool_configs[tool_name] = parse_solver_or_tool_config(tool_cfg)
        # return CoordinationSolverConfig(planner, executor, coder, strategy, coordination_kwargs)
        return CoordinationSolverConfig(tool_configs, strategy, coordination_kwargs)
