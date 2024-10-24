import typing
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from abc import ABC, abstractmethod

@dataclass_json
@dataclass
class GenerationResult(object):
    input_text: str
    generated_text: typing.List[str] = field(default_factory=list)
    neg_log_likelihood: typing.List[float] = field(default_factory=list) # TODO: remove completely

@dataclass_json
@dataclass
class GenerationResults(object):
    results: typing.List[GenerationResult] = field(default_factory=list)

    def __iter__(self):
        return iter(self.results)
    
    def __getitem__(self, key):
        assert isinstance(key, int), "Please provide an integer key"
        return self.results[key]

class Model(ABC):

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def generate(self, inputs: typing.Union[typing.List[typing.List[typing.Dict[str, str]]], typing.List[typing.Dict[str, str]]], **kwargs) -> GenerationResults:
        pass

    @abstractmethod
    def parse_out(self, response: GenerationResults) -> typing.List[typing.List[str]]:
        pass
