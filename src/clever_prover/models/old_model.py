# import os
# import torch
# import typing
# import logging
# import json
# import random
# import shutil
# from enum import Enum
# from torch.utils.data import Dataset, DataLoader
# from transformers import (
#     AutoModelForSeq2SeqLM,
#     AutoModelForCausalLM,
#     AutoTokenizer,
#     BitsAndBytesConfig,
#     DataCollatorForSeq2Seq,
#     RobertaTokenizer,
#     StoppingCriteria,
#     StoppingCriteriaList,
#     TrainingArguments,
#     TrainerCallback,
#     GenerationConfig
# )
# from clever_prover.tools.log_utils import setup_logger
# from transformers.trainer_callback import TrainerControl, TrainerState
# from peft import LoraConfig
# from clever_prover.models.huggingface_model_map import get_empty_config, trim_model_kwargs, get_model_class, get_decoder_start_token_id
# from clever_prover.models.cuda_context import CudaContext
# MODEL_TRAINING_MODE = False # Set this to true while training
# if MODEL_TRAINING_MODE:
#     from clever_prover.models.comet_helper import CometHelper
#     from comet_ml import Experiment
#     from clever_prover.models.custom_sft_trainer import GenerateEvalSFTTrainer
#     from clever_prover.models.custom_s2s_trainer import GenerateEvalS2STrainer
# from clever_prover.models.abs_model import GenerationResult, GenerationResults, Model

# class AutoRegressiveSequenceSearch(Enum):
#     NucleusSampling = "nucleus_sampling"
#     BeamSearch = "beam_search"
#     def __str__(self):
#         return self.value

# class TrainingDataFormatterCallback:
#     def __init__(self):
#         pass
    
#     def __call__(self, training_data_example: typing.Any) -> typing.List[str]:
#         raise NotImplementedError
    
#     def get_prompt_and_completion(self, training_data_example: typing.Any) -> typing.List[typing.Tuple[str, str]]:
#         raise NotImplementedError
    
#     def get_stopping_token(self):
#         raise NotImplementedError

# class LogMetricCallback(TrainerCallback):
#     def __init__(self, model: "Model"):
#         self.model = model
#         self._idx = 0

#     def on_step_end(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
#         # Check if we should run evaluation
#         if state.global_step == 2 and not self.model._no_init_eval: # Just force evaluation at the beginning to ensure that the model is working
#             control.should_log = True
#             control.should_evaluate = True
#         super().on_step_end(args, state, control, **kwargs)
#         return control

#     def on_log(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
#         if len(state.log_history) > 0:
#             metrices = state.log_history[self._idx:]
#             for metrics in metrices:
#                 if self.model._should_use_comet:
#                     self.model._comet_experiment.log_metrics(metrics, step=state.global_step, epoch=state.epoch)
#                 metric_json = json.dumps(metrics)
#                 self.model.metric_logger.info(metric_json)
#             self._idx = len(state.log_history)
#         super().on_log(args, state, control, **kwargs)

# class StopOnTokens(StoppingCriteria):
#     """Stopping criteria based on a list of tokens"""
#     def __init__(self, stop_tokens: typing.List[str], tokenizer: AutoTokenizer, input_length: int):
#         self.stop_token_ids = stop_tokens
#         # self.input_length = input_length
#         self.tokenizer = tokenizer
#         self.stop_tokens = stop_tokens
#         self.cuda_context = CudaContext.get_default_context()
#         stop_token_ids = [self.tokenizer.encode(stop_word, add_special_tokens=False)
#                     for stop_word in self.stop_tokens]
#         stop_token_ids = [self.cuda_context.try_get_gpu(torch.LongTensor(x)) for x in stop_token_ids]
#         self.max_stop_token_id_length = max([len(x) for x in self.stop_token_ids])
#         self.pad_token_tensor = self.cuda_context.try_get_gpu(torch.LongTensor([self.tokenizer.pad_token_id]))
#         self.stop_decisions = {}
#         self.input_length = input_length

#     def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
#         if input_ids.shape[-1] <= self.input_length and not isinstance(self.tokenizer, RobertaTokenizer):
#             return False
#         stop_decisions = [-1] * input_ids.shape[0]
#         for idx in range(input_ids.shape[0]):
#             input_ids_slice = input_ids[idx][-self.max_stop_token_id_length:]
#             stop_decisions[idx] = self.stop_decisions.get(idx, -1)
#             if len(input_ids_slice.shape) > 0 and stop_decisions[idx] == -1:
#                 decoded_slice = self.tokenizer.decode(input_ids_slice)
#                 for stop_token in self.stop_tokens:
#                     if decoded_slice.endswith(stop_token):
#                         stop_decisions[idx] = len(input_ids[idx])
#                         self.stop_decisions[idx] = stop_decisions[idx]
#             elif stop_decisions[idx] != -1:
#                 # Fill the rest of the sequence with the pad token
#                 # Change input_ids[idx][stop_decisions[idx]:] to the pad token
#                 for i in range(stop_decisions[idx], len(input_ids[idx])):
#                     input_ids[idx][i] = self.pad_token_tensor
#         return all([x != -1 for x in stop_decisions])

# class OldModel(Model):
#     """Wrapper for a Llama model"""

#     def __init__(self, name: str, training_args: TrainingArguments = None, log_folder: str = None, **kwargs):
#         assert name is not None, "Please provide a model name"
#         self.name = name
#         self.cuda_context = CudaContext.get_default_context()
#         self.training_args = training_args
#         code_logger = logging.getLogger("ModelCode") if log_folder is None else setup_logger("ModelCode", f"{log_folder}/model_code.log")
#         metric_format = '{"time": "%(asctime)s", "metrics": %(message)s}'
#         metric_logger = logging.getLogger("ModelMetrics") if log_folder is None else setup_logger("ModelMetrics", f"{log_folder}/model_metrics.jsonl", format=metric_format)
#         self.code_logger = code_logger
#         self.metric_logger = metric_logger
#         self._is_loaded = False
#         self._kwargs = kwargs
#         self._should_load_model = self._kwargs.get("load_model", True)
#         self._should_use_lora = self._kwargs.get("use_lora", True)
#         self._comet_experiment_name = self._kwargs.get("comet_experiment", None)
#         self._should_use_comet = self._comet_experiment_name is not None
#         self._is_seq2seq = self._kwargs.get("is_seq2seq", False)
#         self._comet_experiment = None
#         self._no_init_eval = self._kwargs.get("no_init_eval", False)
#         self._random_init = self._kwargs.get("random_init", False)
#         if self._random_init:
#             assert "config_class_name" in self._kwargs, "Please provide the config class name for random initialization"
#         self._config_class_name = self._kwargs.get("config_class_name", None)
#         if "base_device" in self._kwargs and "device_map" in self._kwargs:
#             device_map = dict(self._kwargs["device_map"])
#             self._kwargs["device_map"] = device_map
#             assert isinstance(self._kwargs["device_map"], dict), "Please provide a dictionary for device_map"
#             assert isinstance(self._kwargs["base_device"], int), "Please provide a valid base_device"
#             for k, v in self._kwargs["device_map"].items():
#                 self._kwargs["device_map"][k] = self._kwargs["base_device"] + v
#         pass

#     def parse_out(self, response):
#         return [[y for y in x.generated_text] for x in response.results]


#     def _get_model_args(self):
#         return {k: v for k, v in self._kwargs.items() if k in
#                 ["token", "quantization_config", "device_map", "torch_dtype", "trust_remote_code"]
#         }

#     def _model_init(self) -> typing.Union[AutoModelForSeq2SeqLM, AutoModelForCausalLM]:
#         model_args = self._get_model_args()
#         if self._random_init:
#             assert self._tokenizer is not None, "Tokenizer is not loaded"
#             # initialize the model with random weights
#             # get the config class from the config class name
#             random_config = get_empty_config(self._config_class_name)
#             random_config.decoder_start_token_id = get_decoder_start_token_id(self._config_class_name, self._tokenizer)
#             model_class = get_model_class(self._config_class_name)
#             model_args = trim_model_kwargs(model_args, self._config_class_name)
#         if self.is_sequence_2_sequence():
#             if self._random_init:
#                 temp_model = model_class(random_config, **model_args)
#             else:
#                 temp_model = AutoModelForSeq2SeqLM.from_pretrained(self.name, **model_args)
#         else:
#             if self._random_init:
#                 temp_model = model_class(random_config, **model_args)
#             else:
#                 temp_model = AutoModelForCausalLM.from_pretrained(self.name, **model_args)
#         return temp_model

#     def load(self):
#         if self._is_loaded:
#             return
#         if self._should_use_lora and "quantization_config" not in self._kwargs:
#             quantization_config = BitsAndBytesConfig(
#                 load_in_4bit=True,
#                 bnb_4bit_quant_type="nf4",
#                 bnb_4bit_compute_dtype=getattr(torch,"float16"),
#                 bnb_4bit_use_double_quant=False,
#             )
#             self._kwargs["quantization_config"] = quantization_config
#         quantization_config: BitsAndBytesConfig = self._kwargs.get("quantization_config", None)
#         if quantization_config is not None and quantization_config.bnb_4bit_compute_dtype == torch.float16 and quantization_config.load_in_4bit:
#             major, _ = torch.cuda.get_device_capability()
#             if major >= 8:
#                 self.code_logger.info("The GPU supports bfloat16: accelerate training with bf16=True")
#         if self._should_use_lora and "lor_config" not in self._kwargs:
#             lora_config = LoraConfig(
#                 lora_alpha=16,
#                 lora_dropout=0.1,
#                 r=64,
#                 bias="none",
#                 task_type="CAUSAL_LM",
#             )
#             self._kwargs["lora_config"] = lora_config
#         tokenizer_args = {k: v for k, v in self._kwargs.items() if k in
#                 ["token", "pad_token", "eos_token", "bos_token", "unk_token", "mask_token", "additional_special_tokens", "max_length", "padding", "truncation", "cls_token", "sep_token", "mask_token", "padding_side"]
#         }
#         self._tokenizer : AutoTokenizer = AutoTokenizer.from_pretrained(self.name, **tokenizer_args)
#         if "llama-2" in self.name.lower():
#             if "pad_token" not in tokenizer_args:
#                 tokenizer_args["pad_token"] = self._tokenizer.eos_token
#             if "padding_side" not in tokenizer_args:
#                 tokenizer_args["padding_side"] = "left" # This is very import for the stop token logic
#             if "cls_token" not in tokenizer_args:
#                 tokenizer_args["cls_token"] = tokenizer_args["pad_token"]
#             if "sep_token" not in tokenizer_args:
#                 tokenizer_args["sep_token"] = tokenizer_args["pad_token"]
#             if "mask_token" not in tokenizer_args:
#                 tokenizer_args["mask_token"] = tokenizer_args["pad_token"]
#         if "deepseek" in self.name.lower():
#             if "pad_token" not in tokenizer_args:
#                 tokenizer_args["pad_token"] = self._tokenizer.eos_token
#             if "padding_side" not in tokenizer_args:
#                 tokenizer_args["padding_side"] = "left" # This is very import for the stop token logic
#         if "pad_token" in tokenizer_args:
#             self._tokenizer.pad_token = tokenizer_args["pad_token"]
#         if "eos_token" in tokenizer_args:
#             self._tokenizer.eos_token = tokenizer_args["eos_token"]
#         if "bos_token" in tokenizer_args:
#             self._tokenizer.bos_token = tokenizer_args["bos_token"]
#         if "unk_token" in tokenizer_args:
#             self._tokenizer.unk_token = tokenizer_args["unk_token"]
#         if "additional_special_tokens" in tokenizer_args:
#             self._tokenizer.additional_special_tokens = tokenizer_args["additional_special_tokens"]
#         if "cls_token" in tokenizer_args:
#             self._tokenizer.cls_token = tokenizer_args["cls_token"]
#         if "sep_token" in tokenizer_args:
#             self._tokenizer.sep_token = tokenizer_args["sep_token"]
#         if "mask_token" in tokenizer_args:
#             self._tokenizer.mask_token = tokenizer_args["mask_token"]
#         if "padding_side" in tokenizer_args:
#             self._tokenizer.padding_side = tokenizer_args["padding_side"]
#         if self._should_load_model:
#             if quantization_config is None:
#                 temp_model = self._model_init()
#                 model_args = self._get_model_args()
#                 if "device_map" not in model_args:
#                     self._model : typing.Union[AutoModelForSeq2SeqLM, AutoModelForCausalLM] = self.cuda_context.try_get_gpu(self._model_init())
#                 else:
#                     self._model = temp_model
#             else:
#                 self._model = self._model_init()
#             if hasattr(self._model, "config"):
#                 if hasattr(self._model.config, "use_cache") and "llama-2" in self.name.lower():
#                     self._model.config.use_cache = False
#                 if hasattr(self._model.config, "pretraining_tp") and "llama-2" in self.name.lower():
#                     self._model.config.pretraining_tp = 1
#         else:
#             self._model = None
#         self._is_loaded = True
#         self._model_args = self._get_model_args()
#         self._tokenizer_args = tokenizer_args
#         if "deepseek" in self.name.lower() and hasattr(self._model, "generation_config"):
#             self._model.generation_config = GenerationConfig.from_pretrained(self.name)
#             self._model.generation_config.pad_token_id = self._model.generation_config.eos_token_id


#     def __enter__(self):
#         self.load()
#         return self
    
#     def __exit__(self, exc_type, exc_value, exc_tb):
#         pass

    
#     def is_sequence_2_sequence(self):
#         return self._is_seq2seq

#     def generate(self, inputs: typing.Union[typing.List[str], str], **kwargs) -> GenerationResults:
#         assert self._is_loaded, "Model or tokenizer is not loaded"
#         assert self._model is not None, "Model is not loaded"
#         if isinstance(inputs, str):
#             inputs = [inputs]
#         stop_tokens_are_present = "stop_tokens" in kwargs
#         if "stop_tokens" in kwargs:
#             stop_tokens = kwargs["stop_tokens"]
#         else:
#             stop_tokens = [self._tokenizer.eos_token]
#         if "auto_regressive_sequence_search" in kwargs:
#             auto_regressive_sequence_search = kwargs["auto_regressive_sequence_search"]
#             assert isinstance(auto_regressive_sequence_search, AutoRegressiveSequenceSearch), "Please provide a valid auto_regressive_sequence_search"
#         else:
#             auto_regressive_sequence_search = AutoRegressiveSequenceSearch.NucleusSampling
#         tokenizer_args = {k: v for k, v in kwargs.items() if k in
#         ["max_length", "padding", "truncation"]}
#         tokenized_input = self._tokenizer(
#             inputs,
#             return_tensors="pt",
#             **tokenizer_args)
#         input_ids=self.cuda_context.try_get_gpu(tokenized_input['input_ids'])
#         attention_mask=self.cuda_context.try_get_gpu(tokenized_input['attention_mask'])
#         max_input_length = input_ids.shape[-1]
#         if "llama-2" in self.name.lower() or stop_tokens_are_present:
#             stopping_criteria = StopOnTokens(stop_tokens, tokenizer=self._tokenizer, input_length=max_input_length)
#             stopping_criteria = StoppingCriteriaList([stopping_criteria])
#         else:
#             stopping_criteria = None
#         if auto_regressive_sequence_search == AutoRegressiveSequenceSearch.NucleusSampling:
#             generate_args = {k: v for k, v in kwargs.items() if k in
#             ["do_sample", "top_k", "top_p", "num_return_sequences", "temperature", "max_new_tokens"]}
#         elif auto_regressive_sequence_search == AutoRegressiveSequenceSearch.BeamSearch:
#             generate_args = {k: v for k, v in kwargs.items() if k in
#             ["num_beams", "num_return_sequences", "max_new_tokens"]}
#         else:
#             raise ValueError(f"Invalid auto_regressive_sequence_search: {auto_regressive_sequence_search}")
#         if "num_return_sequences" not in generate_args:
#             generate_args["num_return_sequences"] = 1
#         num_return_sequences = generate_args["num_return_sequences"]
#         if "llama-2" in self.name.lower() or "deepseek" in self.name.lower():
#             generated_output = self._model.generate(
#                 input_ids=input_ids,
#                 attention_mask=attention_mask,
#                 stopping_criteria=stopping_criteria,
#                 eos_token_id=self._tokenizer.eos_token_id,
#                 return_dict_in_generate=True,
#                 **generate_args)
#         else:
#             generated_output = self._model.generate(
#                 input_ids=input_ids,
#                 attention_mask=attention_mask,
#                 stopping_criteria=stopping_criteria,
#                 return_dict_in_generate=True,
#                 **generate_args)
#         target = generated_output["sequences"]
#         return_full_text = kwargs.get("return_full_text", False)
#         if not self.is_sequence_2_sequence() and not return_full_text and ("llama-2" in self.name.lower() or "deepseek" in self.name.lower()):
#             # Replace the target with padding tokens after the input_ids
#             target[:, :max_input_length] = self._tokenizer.pad_token_id # This helps in removing the input text from the generated text
#         skip_special_tokens = kwargs.get("skip_special_tokens", True)
#         decoded_str = self._tokenizer.batch_decode(target, skip_special_tokens=skip_special_tokens)
#         idx = 0
#         generation_results = GenerationResults()
#         compute_probabilities = kwargs.get("compute_probabilities", False)
#         neg_log_likelihoods = []
#         if compute_probabilities:
#             # no gradient computation
#             with torch.no_grad():
#                 for i in range(len(inputs)):
#                     inp_i = input_ids[i, :].unsqueeze(0)
#                     attention_i = attention_mask[i, :].unsqueeze(0)
#                     for j in range(num_return_sequences):
#                         target_j = target[i*num_return_sequences+j].unsqueeze(0)
#                         if "deepseek" in self.name.lower() or "llama-2" in self.name.lower():
#                             # pad the input_ids to match the target length
#                             remaining_length = target_j.shape[-1] - inp_i.shape[-1]
#                             if remaining_length > 0:
#                                 # Pad the input_ids and make sure that they are on the same device
#                                 inp_i = torch.cat([inp_i, torch.full((1, remaining_length), self._tokenizer.pad_token_id, dtype=torch.long, device=inp_i.device)], dim=-1)
#                                 attention_i = torch.cat([attention_i, torch.full((1, remaining_length), 0, dtype=torch.long, device=attention_i.device)], dim=-1)
#                             elif remaining_length < 0:
#                                 # Trim the input_ids
#                                 inp_i = inp_i[:, :target_j.shape[-1]]
#                                 attention_i = attention_i[:, :target_j.shape[-1]]

#                         out_j = self._model(input_ids=inp_i, attention_mask=attention_i, labels=target_j)
#                         neg_log_likelihoods.append(float(out_j.loss.detach().cpu().numpy()))
#         for text in inputs:
#             generated_text = decoded_str[idx: idx + num_return_sequences]
#             if compute_probabilities:
#                 probabilties = neg_log_likelihoods[idx: idx + num_return_sequences]
#             else:
#                 probabilties = [0.0 for _ in range(num_return_sequences)]
#             idx += num_return_sequences
#             result = GenerationResult(input_text=text, generated_text=generated_text, neg_log_likelihood=probabilties)
#             generation_results.results.append(result)
#         return generation_results
   
#     def _generate_completion_callback(self, formatter_callback: TrainingDataFormatterCallback):
#         def _callback(dataset: Dataset):
#             prompts_and_completions = formatter_callback.get_prompt_and_completion(dataset)
#             batch_prompts = [x[0] for x in prompts_and_completions]
#             batch_completions = [x[1] for x in prompts_and_completions]
#             batch_completions_tokenized = self._tokenizer(batch_completions, return_tensors="pt", padding=True, return_length=True)
#             max_new_tokens = max(batch_completions_tokenized["length"])
#             stop_tokens = [formatter_callback.get_stopping_token(), self._tokenizer.eos_token]
#             # Remove the stop tokens which empty
#             stop_tokens = [x for x in stop_tokens if x is not None and isinstance(x, str) and x != ""]
#             # Now generate all the completions
#             generated_completions = self.generate(batch_prompts,
#                             max_new_tokens=max_new_tokens,
#                             temperature=0.1, # Nucleus sampling
#                             do_sample=True, # Nucleus sampling
#                             top_k=5, # Nucleus sampling
#                             # num_beams=5, # Beam search
#                             num_return_sequences=1,
#                             stop_tokens=stop_tokens,
#                             padding=True,
#                             #truncation=True,
#                             return_full_text=False)
#             # Now compare the completions
#             labels = batch_completions
#             preds = [gen_res.generated_text for gen_res in generated_completions]
#             return batch_prompts, labels, preds
#         return _callback

#     def _exact_match_metric_callback(self, datasets, formatter_callback: TrainingDataFormatterCallback, completion_callback: typing.Callable[[Dataset], typing.Tuple[typing.List[str], typing.List[str], typing.List[str]]]):
#         actual_eval_datasets = datasets
#         def _callback(batch_size: int, trainer_state: TrainerState):
#             nonlocal actual_eval_datasets
#             if actual_eval_datasets is None:
#                 return {}
#             if not isinstance(actual_eval_datasets, dict):
#                 eval_datasets = {"eval_dataset": actual_eval_datasets}
#             avg = {
#                 'exact_match': 0.0
#             }
#             for eval_dataset_name in eval_datasets:
#                 eval_dataset = eval_datasets[eval_dataset_name]
#                 # create a dataloader with batch_size
#                 dataloader = DataLoader(eval_dataset, batch_size=batch_size, shuffle=False)
#                 all_prompts = []
#                 all_completions = []
#                 all_predictions = []
#                 correct_pred_idx = []
#                 for batch_idx, dataset in enumerate(dataloader):
#                     prompts_and_completions = formatter_callback.get_prompt_and_completion(dataset)
#                     batch_prompts = [x[0] for x in prompts_and_completions]
#                     batch_completions = [x[1] for x in prompts_and_completions]
#                     all_prompts.extend(batch_prompts)
#                     all_completions.extend(batch_completions)
#                     batch_completions_tokenized = self._tokenizer(batch_completions, return_tensors="pt", padding=True, return_length=True)
#                     max_new_tokens = max(batch_completions_tokenized["length"])
#                     # Now generate all the completions
#                     generated_completions = self.generate(batch_prompts,
#                                     max_new_tokens=max_new_tokens,
#                                     temperature=0.1, # Nucleus sampling
#                                     do_sample=True, # Nucleus sampling
#                                     top_k=5, # Nucleus sampling
#                                     # num_beams=5, # Beam search
#                                     num_return_sequences=1,
#                                     stop_tokens=[formatter_callback.get_stopping_token(), self._tokenizer.eos_token],
#                                     padding=True,
#                                     #truncation=True,
#                                     return_full_text=False)
#                     # Now compare the completions
#                     labels = batch_completions
#                     preds = [gen_res.generated_text[0] for gen_res in generated_completions]
#                     all_predictions.extend(preds)
#                     for _idx, (label, pred) in enumerate(zip(labels, preds)):
#                         if label == pred:
#                             correct_pred_idx.append(batch_idx * batch_size + _idx)
#                 # Calculate Exact Match (EM)
#                 wrong_pred_idx = list(set(range(len(all_completions))) - set(correct_pred_idx))
#                 em = len(correct_pred_idx) / len(all_completions)
#                 avg['exact_match'] += em
#                 prefix = f"[Step = {trainer_state.global_step}] [Epoch = {trainer_state.epoch}] [Dataset = {eval_dataset_name}]"
#                 self.code_logger.info(f"{prefix} [EM = {em}]")
#                 # Sample some examples and log them
#                 min_num_examples = 20
#                 sampled_correct_pred_idx = random.sample(correct_pred_idx, min(min_num_examples, len(correct_pred_idx)))
#                 for _idx in sampled_correct_pred_idx:
#                     self.code_logger.info(f"{prefix} Prompt [{_idx + 1}]: {all_prompts[_idx]}")
#                     self.code_logger.info(f"{prefix} Label [{_idx + 1}]: {all_completions[_idx]}")
#                     self.code_logger.info(f"{prefix} Correct Prediction [{_idx + 1}]: {all_predictions[_idx]}")
#                     if self._comet_experiment:
#                         full_text = f"{prefix}\nPrompt:\n{all_prompts[_idx]}\nLabel:\n{all_completions[_idx]}\nCorrect Prediction:\n{all_predictions[_idx]}"
#                         self._comet_experiment.log_text(full_text, step=trainer_state.global_step, metadata={"type": "correct_prediction"})
#                 sampled_wrong_pred_idx = random.sample(wrong_pred_idx, min(min_num_examples, len(wrong_pred_idx)))
#                 for _idx in sampled_wrong_pred_idx:
#                     self.code_logger.info(f"{prefix} Prompt [{_idx + 1}]: {all_prompts[_idx]}")
#                     self.code_logger.info(f"{prefix} Label [{_idx + 1}]: {all_completions[_idx]}")
#                     self.code_logger.info(f"{prefix} Wrong Prediction [{_idx + 1}]: {all_predictions[_idx]}")
#                     if self._comet_experiment:
#                         full_text = f"{prefix}\nPrompt:\n{all_prompts[_idx]}\nLabel:\n{all_completions[_idx]}\nWrong Prediction:\n{all_predictions[_idx]}"
#                         self._comet_experiment.log_text(full_text, step=trainer_state.global_step, metadata={"type": "wrong_prediction"})
#             avg['exact_match'] /= len(eval_datasets)
#             return avg
#         return _callback
    
#     def _generative_compute_metrics(self):
#         def _compute_metrics_callback(
#                 eval_dataset_name: str,
#                 trainer_state: TrainerState,
#                 prompts: typing.List[str],
#                 labels: typing.List[str],
#                 completions: typing.List[typing.List[str]]):
#                 avg = {'exact_match': 0.0}
#                 correct_pred_idx = []
#                 for _idx, (label, completion) in enumerate(zip(labels, completions)):
#                     for _completion in completion:
#                         if label == _completion:
#                             correct_pred_idx.append(_idx)
#                             break
#                 wrong_pred_idx = list(set(range(len(labels))) - set(correct_pred_idx))
#                 em = len(correct_pred_idx) / len(labels)
#                 avg['exact_match'] += em
#                 prefix = f"[Step = {trainer_state.global_step}] [Epoch = {trainer_state.epoch}] [Dataset = {eval_dataset_name}]"
#                 self.code_logger.info(f"{prefix} [EM = {em}]")
#                 # Sample some examples and log them
#                 min_num_examples = 15
#                 sampled_correct_pred_idx = random.sample(correct_pred_idx, min(min_num_examples, len(correct_pred_idx)))
#                 for _idx in sampled_correct_pred_idx:
#                     self.code_logger.info(f"{prefix} Prompt [{_idx + 1}]: {prompts[_idx]}")
#                     self.code_logger.info(f"{prefix} Label [{_idx + 1}]: {labels[_idx]}")
#                     self.code_logger.info(f"{prefix} Correct Prediction [{_idx + 1}]: {completions[_idx]}")
#                     if self._comet_experiment:
#                         full_text = f"{prefix}\nPrompt:\n{prompts[_idx]}\nLabel:\n{labels[_idx]}\nCorrect Prediction:\n{completions[_idx]}"
#                         self._comet_experiment.log_text(full_text, step=trainer_state.global_step, metadata={"type": "correct_prediction"})
#                 sampled_wrong_pred_idx = random.sample(wrong_pred_idx, min(min_num_examples, len(wrong_pred_idx)))
#                 for _idx in sampled_wrong_pred_idx:
#                     self.code_logger.info(f"{prefix} Prompt [{_idx + 1}]: {prompts[_idx]}")
#                     self.code_logger.info(f"{prefix} Label [{_idx + 1}]: {labels[_idx]}")
#                     self.code_logger.info(f"{prefix} Wrong Prediction [{_idx + 1}]: {completions[_idx]}")
#                     if self._comet_experiment:
#                         full_text = f"{prefix}\nPrompt:\n{prompts[_idx]}\nLabel:\n{labels[_idx]}\nWrong Prediction:\n{completions[_idx]}"
#                         self._comet_experiment.log_text(full_text, step=trainer_state.global_step, metadata={"type": "wrong_prediction"})
#                 return avg
#         return _compute_metrics_callback
    
#     def _log_metric_callback(self) -> TrainerCallback:
#         return LogMetricCallback(self)

#     def _seq2seq_tokenizer(self, dataset: Dataset, training_data_formatter_callback: TrainingDataFormatterCallback, max_seq_length: int = 512):
#         prompts_and_completions = training_data_formatter_callback.get_prompt_and_completion(dataset)
#         inputs = [x[0] for x in prompts_and_completions]
#         labels = [x[1] for x in prompts_and_completions]
#         tokenizer_args = {k: v for k, v in self._tokenizer_args.items() if k in
#         ["max_length", "padding", "truncation"]}
#         model_inputs = self._tokenizer(inputs, return_tensors="pt", **tokenizer_args)
#         label_args = {k: v for k, v in self._tokenizer_args.items() if k in
#         ["padding", "truncation"]}
#         label_args["max_length"] = max_seq_length
#         model_labels = self._tokenizer(labels, return_tensors="pt", **label_args)
#         model_inputs["labels"] = model_labels["input_ids"]
#         return model_inputs

#     def train(self,
#             time_str: str,
#             training_data_formatter_callback: TrainingDataFormatterCallback,
#             train_dataset: Dataset,
#             eval_dataset: typing.Union[Dataset, typing.Dict[str, Dataset]] = None,
#             compute_metrics: typing.Optional[typing.Callable[[str, TrainerState, typing.List[str], typing.List[str], typing.List[typing.List[str]]], typing.Dict]] = None,
#             callbacks: typing.List[TrainerCallback] = None):
#         assert self._is_loaded, "Model or tokenizer is not loaded"
#         assert self.training_args is not None, "Please provide training arguments"
#         if compute_metrics is None:
#             compute_metrics = self._generative_compute_metrics()
#             # paramless_compute_metrics = self._exact_match_metric_callback(eval_dataset, training_data_formatter_callback)
#         if callbacks is None:
#             callbacks = []
#         # unload the model from the GPU
#         self.cuda_context.free_cuda_cache_if_possible()
#         lora_config = self._kwargs.get("lora_config", None)
#         max_seq_length = self._kwargs.get("max_seq_length", None)
#         if self._should_use_comet:
#             self._comet_helper = CometHelper()
#             self._comet_experiment : Experiment = self._comet_helper.get_experiment(self._comet_experiment_name)
#             # Check if the experiment exists
#             self._comet_experiment.log_parameters(self._kwargs)
#         if self.is_sequence_2_sequence():
#             data_collator = DataCollatorForSeq2Seq(tokenizer=self._tokenizer, model=self._model)
#             trainer = GenerateEvalS2STrainer(
#                 model=(self.name if self._model is None else self._model), # This will anyway create a new model
#                 args=self.training_args,
#                 data_collator=data_collator,
#                 train_dataset=train_dataset,
#                 eval_dataset=eval_dataset,
#                 tokenizer=self._tokenizer,
#                 callbacks=callbacks,
#                 preprocess_logits_for_metrics=(lambda _x, _y: fake_logit_tensor), # no need to compute logits and reduce memory usage
#                 tokenizer_func=lambda x: self._seq2seq_tokenizer(x, training_data_formatter_callback, max_seq_length=max_seq_length),
#                 generate_callback=self._generate_completion_callback(training_data_formatter_callback),
#                 generative_compute_metrics=compute_metrics,
#                 logger=self.code_logger,
#                 model_init=self._model_init if self._random_init else None,
#             )
#         else:
#             fake_logit_tensor = torch.tensor([0.0])
#             trainer = GenerateEvalSFTTrainer(
#                 model=(self.name if self._model is None else self._model), # This will anyway create a new model
#                 args=self.training_args,
#                 # data_collator=self._collate_fn,
#                 train_dataset=train_dataset,
#                 eval_dataset=eval_dataset,
#                 tokenizer=self._tokenizer,
#                 callbacks=callbacks,
#                 # dataset_text_field="text",
#                 packing=False,
#                 dataset_batch_size=self.training_args.train_batch_size,
#                 formatting_func=training_data_formatter_callback.__call__,
#                 model_init_kwargs=self._model_args if self._model is None else None,
#                 peft_config=lora_config,
#                 max_seq_length=max_seq_length,
#                 preprocess_logits_for_metrics=(lambda _x, _y: fake_logit_tensor), # no need to compute logits and reduce memory usage
#                 generate_callback=self._generate_completion_callback(training_data_formatter_callback),
#                 generative_compute_metrics=compute_metrics,
#                 logger=self.code_logger,
#                 model_init=self._model_init if self._random_init else None,
#             )
#         trainer.add_callback(self._log_metric_callback())
#         if self.training_args.do_train:
#             if self.training_args.resume_from_checkpoint is not None:
#                 trainer.train(resume_from_checkpoint=self.training_args.resume_from_checkpoint) # Resume from a specific checkpoint
#             else:
#                 # Check if a checkpoint exists
#                 no_checkpoint = True
#                 try:
#                     trainer.train(resume_from_checkpoint=True)
#                 except:
#                     # Eat the exception
#                     no_checkpoint = True
#                 if no_checkpoint:
#                     trainer.train()
#         if self.training_args.do_eval and eval_dataset is not None:
#             self.code_logger.info("Running evaluation after training")
#             trainer.evaluate()
#         # Change the model name and save it
#         # load the best model
#         if self.training_args.do_train:
#             os.makedirs(self.training_args.output_dir, exist_ok=True)
#             new_model_name = os.path.join(self.training_args.output_dir, f"best-model-{time_str}")
#             if os.path.exists(new_model_name):
#                 shutil.move(new_model_name, f"{new_model_name}-before-{time_str}")
#             os.makedirs(new_model_name, exist_ok=True)
#         if self.training_args.load_best_model_at_end and trainer.state.best_model_checkpoint is not None and self.training_args.do_train:
#             # Copy the best model to a new model
#             best_model_path = trainer.state.best_model_checkpoint
#             # Recursively copy the best model
#             self.code_logger.info(f"Copying the best model from {best_model_path} to {new_model_name}")
#             shutil.copytree(best_model_path, new_model_name, dirs_exist_ok=True)
#         else:
#             best_model_path = None
#         if best_model_path is None and self.training_args.do_train:
#             trainer.args.output_dir = new_model_name
#             self.code_logger.info(f"Saving the model to {new_model_name}")
#             trainer.save_model()
#         if self._should_use_comet:
#             self._comet_experiment.end()

# if __name__ == '__main__':
#     # Model from Hugging Face hub
#     import os
#     import numpy as np
#     import json
#     # assert os.path.exists(".secrets/huggingface_token.json"), "Please create a .secrets file with your HF token"
#     # model_name = "meta-llama/Llama-2-7b-hf"
#     # model_name = "meta-llama/Llama-2-7b-chat-hf"
#     # model_name = "Salesforce/codet5-small"
#     # device_map = None
#     model_name = "deepseek-ai/deepseek-math-7b-base"
#     device_map = [('model.embed_tokens', 0),
#                  ('model.layers.0', 0),
#                  ('model.layers.1', 0),
#                  ('model.layers.2', 0),
#                  ('model.layers.3', 1),
#                  ('model.layers.4', 1),
#                  ('model.layers.5', 1),
#                  ('model.layers.6', 1),
#                  ('model.layers.7', 1),
#                  ('model.layers.8', 1),
#                  ('model.layers.9', 1),
#                  ('model.layers.10', 1),
#                  ('model.layers.11', 1),
#                  ('model.layers.12', 1),
#                  ('model.layers.13', 1),
#                  ('model.layers.14', 2),
#                  ('model.layers.15', 2),
#                  ('model.layers.16', 2),
#                  ('model.layers.17', 2),
#                  ('model.layers.18', 2),
#                  ('model.layers.19', 2),
#                  ('model.layers.20', 2),
#                  ('model.layers.21', 2),
#                  ('model.layers.22', 3),
#                  ('model.layers.23', 3),
#                  ('model.layers.24', 3),
#                  ('model.layers.25', 3),
#                  ('model.layers.26', 3),
#                  ('model.layers.27', 3),
#                  ('model.layers.28', 3),
#                  ('model.layers.29', 3),
#                  ('model.norm', 3),
#                  ('lm_head', 3)]
#     base_device = 3
#     device_map = {x[0]: x[1] + base_device for x in device_map}
#     is_seq2seq = "t5" in model_name.lower()
#     token = None
#     if device_map is not None:
#         model = OldModel(model_name, token=token, use_lora=False, is_seq2seq=is_seq2seq, device_map=device_map)
#     else:
#         model = OldModel(model_name, token=token, use_lora=False, is_seq2seq=is_seq2seq)
#     main_prompt = "Do simple math problems (Answer only the number and use '[END]' to finish the response):\nQuestion: 2 + 2\nAnswer: 4\n[END]"
#     with model:
#         for response in model.generate(
#                 [
#                     f"{main_prompt}\nQuestion: 4 + 5\nAnswer:",
#                     f"{main_prompt}\nQuestion: 2 + 2\nAnswer:",
#                     f"{main_prompt}\nQuestion: 3 + 3 * 3\nAnswer:",
#                 ],
#                 max_new_tokens=10,
#                 temperature=0.1, # Nucleus sampling
#                 do_sample=True, # Nucleus sampling
#                 top_k=5, # Nucleus sampling
#                 # num_beams=5, # Beam search
#                 num_return_sequences=5,
#                 stop_tokens=["[END]"],#, model._tokenizer.eos_token],
#                 skip_special_tokens=True,
#                 padding=True,
#                 #truncation=True,
#                 compute_probabilities=True,
#                 return_full_text=False):
            
#             print("-" * 50)
#             print(f"Prompt: \n{response.input_text}")
#             for idx, result in enumerate(response.generated_text):
#                 probability = np.exp(-response.neg_log_likelihood[idx])
#                 print(f"Result [{idx + 1}] ({probability*100}% chance): {result}")
#             print("-" * 50)
