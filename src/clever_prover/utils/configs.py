from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Optional, Dict, Any, List

@dataclass_json
@dataclass
class PromptSettings:
    system_prompt_path: str
    example_prompt_path: str
    max_tokens_per_action: int
    max_history_messages: int
    end_tokens: List[str] = field(default_factory=list)

@dataclass_json
@dataclass
class ModelSettings:
    model_name: str
    secret_path: str
    temperature: float


