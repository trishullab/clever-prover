import typing
from abc import ABC, abstractmethod

class Prompt(ABC):
    def __init__(self, 
        system_prompt_path: str = None, 
        example_prompt_path: str = None, 
        system_prompt: str = None, 
        example_prompt: str = None,
        append_system_prompt_after_every_message: bool = False
    ):
        # assert not all([_ is None for _ in [system_prompt_path, system_prompt]]) and not all([_ is None for _ in [example_prompt_path, example_prompt]]), "Either system_prompt_path or system_prompt must be provided, and either example_prompt_path or example_prompt must be provided."
        self.system_prompt_path = system_prompt_path
        self.example_prompt_path = example_prompt_path
        self.system_prompt = system_prompt
        self.append_system_prompt_after_every_message = append_system_prompt_after_every_message
        self.example_prompt = example_prompt
        if self.system_prompt is None and self.system_prompt_path is not None:
            with open(self.system_prompt_path, "r") as f:
                self.system_prompt = f.read()
        if self.example_prompt is None and self.example_prompt is not None:
            with open(self.example_prompt_path, "r") as f:
                self.example_prompt = f.read()


    def translate_for_deepseek(self, messages):
        last_role = None
        seen_user_role_before = False

        prompt = ''
        for message in messages:
            if message['role'] == 'user':

                if last_role == 'assistant':
                    prompt += '<｜end▁of▁sentence｜>'
                # if self.system_prompt is not None and (self.append_system_prompt_after_every_message or not seen_user_role_before):
                #     # prompt += f'User: {self.system_prompt}{message["content"]}\n'
                #     prompt += f"User: {self.system_prompt.format(message['content']).strip()}\n"
                # else:
                #     prompt += f'User: {message["content"].strip()}\n'
                prompt += f'User: {message["content"].strip()}\n'
                last_role = 'user'
                seen_user_role_before = True
            elif message['role'] == 'assistant':
                prompt += f'Assistant: {message["content"].strip()}\n'
                last_role = 'assistant'
        if last_role == 'user':
            prompt += 'Assistant:'
        return prompt


    @abstractmethod
    def get_prompt(self, messages: typing.List[typing.Dict[str, str]]) -> str:
        pass

    @abstractmethod
    def parse_response(self, response: str) -> str:
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
                full_prompt += f"\n{k}\n{v}"
        return full_prompt + "\n"
    
    def parse_response(self, response: str) -> str:
        return response