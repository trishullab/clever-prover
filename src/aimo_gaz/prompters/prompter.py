import typing
from abc import ABC, abstractmethod
from aimo_gaz.utils import string_utils

class Prompter(ABC):
    def __init__(self,
        system_prompt_path: str = None,
        example_prompt_path: str = None,
        system_prompt: str = None,
        example_prompt_list: list[dict[str, str]] = None,
        append_system_prompt_after_every_message: bool = False,
    ):
        # assert not all([_ is None for _ in [system_prompt_path, system_prompt]]) and not all([_ is None for _ in [example_prompt_path, example_prompt_list]]), "Either system_prompt_path or system_prompt must be provided, and either example_prompt_path or example_prompt_list must be provided."
        assert not all([_ is None for _ in [system_prompt_path, system_prompt]]), "Either system_prompt_path or system_prompt must be provided."
        self.system_prompt_path = system_prompt_path
        self.example_prompt_path = example_prompt_path
        self.system_prompt = system_prompt
        self.append_system_prompt_after_every_message = append_system_prompt_after_every_message
        self.example_prompt_list = example_prompt_list
        if self.system_prompt is None and self.system_prompt_path is not None:
            with open(self.system_prompt_path, "r") as f:
                self.system_prompt = f.read()
        if self.example_prompt_list is None and self.example_prompt_path is not None:
            with open(self.example_prompt_path, "r") as f:
                example_prompt_str = f.read()
                self.example_prompt_list = string_utils.parse_example_prompt_list(example_prompt_str)
        
        self.stop_tokens = []

    # def translate_for_deepseek(self, history, no_newline_after_assistant=False):
    #     last_role = None
    #     seen_user_role_before = False

    #     prompt = ''
    #     is_last_message = False
    #     msg_count = 0
    #     for message in history:
    #         msg_count += 1
    #         is_last_message = msg_count == len(history)
    #         if message['role'] == 'user':

    #             if last_role == 'assistant':
    #                 prompt += '<｜end▁of▁sentence｜>'
    #             # if self.system_prompt is not None and (self.append_system_prompt_after_every_message or not seen_user_role_before):
    #             #     # prompt += f'User: {self.system_prompt}{message["content"]}\n'
    #             #     prompt += f"User: {self.system_prompt.format(message['content']).strip()}\n"
    #             # else:
    #             #     prompt += f'User: {message["content"].strip()}\n'
    #             prompt += f'User: {message["content"].strip()}\n'
    #             last_role = 'user'
    #             seen_user_role_before = True
    #         elif message['role'] == 'assistant':
    #             if no_newline_after_assistant and is_last_message:
    #                 prompt += f'Assistant: {message["content"].strip()}'
    #             else:
    #                 prompt += f'Assistant: {message["content"].strip()}\n'
    #             last_role = 'assistant'
    #     if last_role == 'user':
    #         prompt += 'Assistant:'
    #     return prompt

    @abstractmethod
    def get_prompt(self, history: typing.List[typing.Dict[str, str]], *args, **kwargs) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def parse_response(self, response: str):
        pass

    def reset_example_prompt(self, example_prompt_list: list[dict[str, str]] = None, example_prompt_path: str = None):
        assert not all([_ is None for _ in [example_prompt_path, example_prompt_list]]), "Either example_prompt_path or example_prompt_list must be provided."
        self.example_prompt_path = example_prompt_path
        self.example_prompt_list = example_prompt_list
        if self.example_prompt_list is None:
            with open(self.example_prompt_path, "r") as f:
                self.example_prompt_list = f.read()
    
    def reset_system_prompt(self, system_prompt: str = None, system_prompt_path: str = None):
        assert not all([_ is None for _ in [system_prompt_path, system_prompt]]), "Either system_prompt_path or system_prompt must be provided."
        self.system_prompt_path = system_prompt_path
        self.system_prompt = system_prompt
        if self.system_prompt is None:
            with open(self.system_prompt_path, "r") as f:
                self.system_prompt = f.read()


# class ConcatPrompter(Prompter):
#     def get_prompt(self, history: typing.List[typing.Dict[str, str]]) -> list[dict[str, str]]:
#         full_prompt = self.system_prompt + "\n" + self.example_prompt
#         for msg in history:
#             for k, v in msg.items():
#                 full_prompt += f"\n{k}\n{v}"
#         return full_prompt + "\n"
    
#     def parse_response(self, response: str) -> str:
#         return response
