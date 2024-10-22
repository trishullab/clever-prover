import typing
from abs_model import GenerationResult, GenerationResults, Model
from gpt_access import GptAccess

class GptModel(Model):
    def __init__(self, name: str, secret_filepath: str = ".secrets/openai_key.json"):
        self.gpt_access = GptAccess(secret_filepath, model_name=name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def generate(self, inputs: typing.Union[typing.List[str], str], **kwargs) -> GenerationResults:
        return GenerationResults()

if __name__ == '__main__':
    # Model from Hugging Face hub
    import os
    import numpy as np
    import json
    # assert os.path.exists(".secrets/huggingface_token.json"), "Please create a .secrets file with your HF token"
    # model_name = "meta-llama/Llama-2-7b-hf"
    # model_name = "meta-llama/Llama-2-7b-chat-hf"
    # model_name = "Salesforce/codet5-small"
    # device_map = None
    model_name = "gpt-4o"
    device_map = [('model.embed_tokens', 0),
                 ('model.layers.0', 0),
                 ('model.layers.1', 0),
                 ('model.layers.2', 0),
                 ('model.layers.3', 1),
                 ('model.layers.4', 1),
                 ('model.layers.5', 1),
                 ('model.layers.6', 1),
                 ('model.layers.7', 1),
                 ('model.layers.8', 1),
                 ('model.layers.9', 1),
                 ('model.layers.10', 1),
                 ('model.layers.11', 1),
                 ('model.layers.12', 1),
                 ('model.layers.13', 1),
                 ('model.layers.14', 2),
                 ('model.layers.15', 2),
                 ('model.layers.16', 2),
                 ('model.layers.17', 2),
                 ('model.layers.18', 2),
                 ('model.layers.19', 2),
                 ('model.layers.20', 2),
                 ('model.layers.21', 2),
                 ('model.layers.22', 3),
                 ('model.layers.23', 3),
                 ('model.layers.24', 3),
                 ('model.layers.25', 3),
                 ('model.layers.26', 3),
                 ('model.layers.27', 3),
                 ('model.layers.28', 3),
                 ('model.layers.29', 3),
                 ('model.norm', 3),
                 ('lm_head', 3)]
    base_device = 3
    device_map = {x[0]: x[1] + base_device for x in device_map}
    is_seq2seq = "t5" in model_name.lower()
    token = None
    if device_map is not None:
        model = GptModel(model_name, token=token, use_lora=False, is_seq2seq=is_seq2seq, device_map=device_map)
    else:
        model = GptModel(model_name, token=token, use_lora=False, is_seq2seq=is_seq2seq)
    main_prompt = "Do simple math problems (Answer only the number and use '[END]' to finish the response):\nQuestion: 2 + 2\nAnswer: 4\n[END]"
    with model:
        for response in model.generate(
                [
                    f"{main_prompt}\nQuestion: 4 + 5\nAnswer:",
                    f"{main_prompt}\nQuestion: 2 + 2\nAnswer:",
                    f"{main_prompt}\nQuestion: 3 + 3 * 3\nAnswer:",
                ],
                max_new_tokens=10,
                temperature=0.1, # Nucleus sampling
                do_sample=True, # Nucleus sampling
                top_k=5, # Nucleus sampling
                # num_beams=5, # Beam search
                num_return_sequences=5,
                stop_tokens=["[END]"],#, model._tokenizer.eos_token],
                skip_special_tokens=True,
                padding=True,
                #truncation=True,
                compute_probabilities=True,
                return_full_text=False):
            
            print("-" * 50)
            print(f"Prompt:\n{response.input_text}")
            for idx, result in enumerate(response.generated_text):
                probability = np.exp(-response.neg_log_likelihood[idx])
                print(f"Result [{idx + 1}] ({probability*100}% chance): {result}")
            print("-" * 50)
