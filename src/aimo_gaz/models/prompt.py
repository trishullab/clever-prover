import typing
from abc import ABC, abstractmethod

class Prompt(ABC):
    def __init__(self, 
        system_prompt_path: str = None, 
        example_prompt_path: str = None, 
        system_prompt: str = None, 
        example_prompt: str = None):
        assert not all([_ is None for _ in [system_prompt_path, system_prompt]]) and not all([_ is None for _ in [example_prompt_path, example_prompt]]), "Either system_prompt_path or system_prompt must be provided, and either example_prompt_path or example_prompt must be provided."
        self.system_prompt_path = system_prompt_path
        self.example_prompt_path = example_prompt_path
        self.system_prompt = system_prompt
        self.example_prompt = example_prompt
        if self.system_prompt is None:
            with open(self.system_prompt_path, "r") as f:
                self.system_prompt = f.read()
        if self.example_prompt is None:
            with open(self.example_prompt_path, "r") as f:
                self.example_prompt = f.read()
    
    @abstractmethod
    def get_prompt(self, messages: typing.List[typing.Dict[str, str]]) -> str:
        pass

    def reset_example_prompt(self, example_prompt: str = None, example_prompt_path: str = None):
        assert not all([_ is None for _ in [example_prompt_path, example_prompt]]), "Either example_prompt_path or example_prompt must be provided."
        self.example_prompt_path = example_prompt_path
        self.example_prompt = example_prompt
        if self.example_prompt is None:
            with open(self.example_prompt_path, "r") as f:
                self.example_prompt = f.read()
    
    def reset_system_prompt(self, system_prompt: str = None, system_prompt_path: str = None):
        assert not all([_ is None for _ in [system_prompt_path, system_prompt]]), "Either system_prompt_path or system_prompt must be provided."
        self.system_prompt_path = system_prompt_path
        self.system_prompt = system_prompt
        if self.system_prompt is None:
            with open(self.system_prompt_path, "r") as f:
                self.system_prompt = f.read()

class ConcatPrompt(Prompt):
    def get_prompt(self, messages: typing.List[typing.Dict[str, str]]) -> str:
        full_prompt = self.system_prompt + "\n" + self.example_prompt
        for msg in messages:
            for k, v in msg.items():
                full_prompt += f"\n{k}: \n{v}"
        return full_prompt + "\n"