#!/usr/bin/env python3

import hydra
import os
import time
import asyncio
import ray
import logging
from clever_bench.task import ProblemViewTask, TaskComponent, ValidationResult
from clever_bench.benchmark import Benchmark
import ray.actor
from clever_prover.tasks.spec_generation_task import GenerationResult
from clever_prover.main.checkpoint import CheckpointWrapper, ExecutionInfo
from clever_prover.main.parse_config import parse_config, parse_spec_generation_class, parse_impl_generation_class, TaskType
from itp_interface.tools.log_utils import setup_logger

def save_checkpoint(problem_idx: int, execution_info: ExecutionInfo, checkpoint_wrapper: CheckpointWrapper, logger: logging.Logger):
    logger.info(f"Saving results for problem {problem_idx} to checkpoint.")
    checkpoint_wrapper.add(execution_info)
    checkpoint_wrapper.save()
    logger.info(f"Checkpoint saved to {checkpoint_wrapper.save_path}")

@ray.remote
def eval_spec_generation(
        cfg, 
        idx: int,
        attempt_idx: int, 
        problem_view: ProblemViewTask, 
        logging_dir: str, 
        hyper_params: dict,
        timeout_in_secs: float,
        compilation_timeout: int,
        checkpoint_actor: ray.actor.ActorHandle, 
        save_path: str):
    if "proof_dump_file_path" in hyper_params:
        filename = hyper_params["proof_dump_file_path"]
        filename = str(os.path.basename(filename))
        filename = filename.split(".")[0]
        final_filename = f"{filename}_{idx}.{filename.split('.')[-1]}"
        hyper_params["proof_dump_file_path"] = os.path.join(logging_dir, final_filename)
    checkpoint_wrapper = CheckpointWrapper(actor=checkpoint_actor, save_path=save_path)
    spec_generation_strategy = parse_spec_generation_class(cfg)
    logger = setup_logger(
        name=f"eval_spec_generation_{idx}", 
        log_file=os.path.join(logging_dir, f"eval_spec_generation_{idx}.log"))
    generation_result = GenerationResult.REGENERATE
    compiled = False
    execution_info = ExecutionInfo(
        problem_id=idx,
        attempt_count=attempt_idx + 1,
        task_type=TaskType.SPEC_ISOMORPHISM,
        generation_time=0,
        proof_time=0,
        total_time=0,
        compiles=False,
        is_proven=False
    )
    skip_proof = False
    skip_checkpoint = False
    validation_result = ValidationResult(
        problem_id=idx,
        isomorphism_ok=False,
        correctness_ok=False,
        compilation_ok=False,
        error_message="",
        lean_code=""
    )
    while generation_result == GenerationResult.REGENERATE and timeout_in_secs > 0:
        spec_generation_task = spec_generation_strategy(
            problem_id=idx,
            problem_view=problem_view,
            logger=logger,
            **hyper_params)
        start_time = time.time()
        try:
            _ = spec_generation_task.generate_specification(timeout_in_ms=timeout_in_secs * 1000, logger=logger)
            skip_proof = False
        except Exception as e:
            logger.error(f"Spec generation failed with exception: {e}")
            logger.error("Spec generation failed. Skipping proof generation.")
            generation_result = GenerationResult.REGENERATE
            skip_proof = True
        finally:
            end_time = time.time()
            generation_time = end_time - start_time
            timeout_in_secs = max(0, timeout_in_secs - generation_time)
        if skip_proof:
            continue
        validation_result = asyncio.run(
            problem_view.submit_async(
                problem=spec_generation_task.generated_spec_problem_view,
                timeout_in_ms=compilation_timeout
            ))
        execution_info.compiles = validation_result.compilation_ok or compiled
        execution_info.is_proven = False
        execution_info.generation_time += generation_time
        execution_info.total_time += generation_time
        logger.info(f"Generation Result:\n{execution_info}")
        if validation_result.compilation_ok:
            logger.info(f"Problem {idx} was compiled successfully.")
            compiled = True
        else:
            logger.error("Spec Generation failed.")
            logger.error(f"Spec Compilation Error: {validation_result.error_message[-300:]}")
            save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
            return validation_result
            # No point in even attempting the proof if the spec generation failed
        logger.info(f"For problem {idx}, proof generation will be attempted.")
        logger.info(f"Time remaining for proof generation: {timeout_in_secs} seconds")
        if timeout_in_secs <= 0:
            logger.error("Timeout for proof generation reached. Skipping proof generation.")
            save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
            return validation_result
        start_time = time.time()
        try:
            generation_result, _ = spec_generation_task.generate_spec_isomorphism_proof(timeout_in_ms=timeout_in_secs * 1000, logger=logger)
            skip_checkpoint = False
        except Exception as e:
            logger.error(f"Proof generation failed with exception: {e}")
            logger.error("Proof generation failed. Skipping proof submission.")
            generation_result = GenerationResult.REGENERATE
            skip_checkpoint = True
        finally:
            end_time = time.time()
            proof_time = end_time - start_time
            timeout_in_secs = max(0, timeout_in_secs - proof_time)
        if skip_checkpoint:
            continue
        # Submit the proof to the problem view
        validation_result = asyncio.run(
            problem_view.submit_async(
                problem=spec_generation_task.generated_proof_problem_view,
                timeout_in_ms=compilation_timeout
            ))
        execution_info.proof_time += proof_time
        execution_info.total_time += proof_time
        execution_info.is_proven = validation_result.isomorphism_ok
        logger.info(f"Proof Generation Result:\n{execution_info}")
        if not validation_result.isomorphism_ok:
            logger.error("Proof failed.")
            if validation_result.error_message:
                logger.error(f"Proof error: {validation_result.error_message[-300:]}")
            generation_result = GenerationResult.REGENERATE
        else:
            logger.info(f"Problem {idx} was solved successfully.")
            break
        logger.info(f"Time remaining {timeout_in_secs} seconds, regenerating spec {generation_result}")
    save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
    return validation_result

@ray.remote
def eval_impl_generation(
        cfg, 
        idx: int,
        attempt_idx: int, 
        problem_view: ProblemViewTask, 
        logging_dir: str, 
        hyper_params: dict,
        timeout_in_secs: float,
        compilation_timeout: int,
        checkpoint_actor: ray.actor.ActorHandle, 
        save_path: str):
    if "proof_dump_file_path" in hyper_params:
        filename = hyper_params["proof_dump_file_path"]
        filename = str(os.path.basename(filename))
        filename = filename.split(".")[0]
        final_filename = f"{filename}_{idx}.{filename.split('.')[-1]}"
        hyper_params["proof_dump_file_path"] = os.path.join(logging_dir, final_filename)
    # Similar to eval_spec_generation but for implementation generation
    checkpoint_wrapper = CheckpointWrapper(actor=checkpoint_actor, save_path=save_path)
    impl_generation_strategy = parse_impl_generation_class(cfg)
    logger = setup_logger(
        name=f"eval_impl_generation_{idx}", 
        log_file=os.path.join(logging_dir, f"eval_impl_generation_{idx}.log"))
    generation_result = GenerationResult.REGENERATE
    compiled = False
    execution_info = ExecutionInfo(
        problem_id=idx,
        attempt_count=attempt_idx + 1,
        task_type=TaskType.IMPL_CORRECTNESS,
        generation_time=0,
        proof_time=0,
        total_time=0,
        compiles=False,
        is_proven=False
    )
    skip_proof = False
    skip_checkpoint = False
    validation_result = ValidationResult(
        problem_id=idx,
        isomorphism_ok=False,
        correctness_ok=False,
        compilation_ok=False,
        error_message="",
        lean_code=""
    )
    while generation_result == GenerationResult.REGENERATE and timeout_in_secs > 0:
        impl_generation_task = impl_generation_strategy(
            problem_id=idx,
            problem_view=problem_view,
            logger=logger,
            **hyper_params)
        start_time = time.time()
        try:
            _ = impl_generation_task.generate_implementation(timeout_in_ms=timeout_in_secs * 1000, logger=logger)
            skip_proof = False
        except Exception as e:
            logger.error(f"Impl generation failed with exception: {e}")
            logger.error("Impl generation failed. Skipping proof generation.")
            generation_result = GenerationResult.REGENERATE
            skip_proof = True
        finally:
            end_time = time.time()
            generation_time = end_time - start_time
            timeout_in_secs = max(0, timeout_in_secs - generation_time)
        if skip_proof:
            continue
        validation_result = asyncio.run(
            problem_view.submit_async(
                problem=impl_generation_task.generated_impl_problem_view,
                timeout_in_ms=compilation_timeout
            ))
        execution_info.compiles = validation_result.compilation_ok or compiled
        execution_info.is_proven = False
        execution_info.generation_time += generation_time
        execution_info.total_time += generation_time
        execution_info.compiles = validation_result.compilation_ok or compiled
        logger.info(f"Generation Result:\n{execution_info}")
        if validation_result.compilation_ok:
            compiled = True
            logger.info(f"Problem {idx} was compiled successfully.")
        else:
            logger.error("Implementation Generation failed.")
            logger.error(f"Implementation Compilation Error: {validation_result.error_message[-300:]}")
            save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
            return validation_result
        logger.info(f"For problem {idx}, proof generation will be attempted.")
        logger.info(f"Time remaining for proof generation: {timeout_in_secs} seconds")
        if timeout_in_secs <= 0:
            logger.error("Timeout for proof generation reached. Skipping proof generation.")
            save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
            return validation_result
        # No point in even attempting the proof if the implementation generation failed
        start_time = time.time()
        try:
            generation_result, _  = impl_generation_task.generate_implementation_correctness_proof(
                timeout_in_ms=timeout_in_secs * 1000, 
                logger=logger)
            skip_checkpoint = False
        except Exception as e:
            logger.error(f"Proof generation failed with exception: {e}")
            logger.error("Proof generation failed. Skipping proof submission.")
            generation_result = GenerationResult.REGENERATE
            skip_checkpoint = True
        finally:            
            end_time = time.time()
            proof_time = end_time - start_time
            timeout_in_secs = max(0, timeout_in_secs - proof_time)
        if skip_checkpoint:
            continue
        # Submit the proof to the problem view
        validation_result = asyncio.run(
            problem_view.submit_async(
                problem=impl_generation_task.generated_proof_problem_view,
                timeout_in_ms=compilation_timeout
            ))
        execution_info.proof_time += proof_time
        execution_info.total_time += proof_time
        execution_info.is_proven = validation_result.correctness_ok
        logger.info(f"Proof Generation Result:\n{execution_info}")
        if not validation_result.correctness_ok:
            logger.error("Proof failed.")
            if validation_result.error_message:
                logger.error(f"Proof error: {validation_result.error_message[-300:]}")
            generation_result = GenerationResult.REGENERATE
        else:
            logger.info(f"Problem {idx} was solved successfully.")
            break
        logger.info(f"Time remaining {timeout_in_secs} seconds, regenerating impl {generation_result}")
    save_checkpoint(idx, execution_info, checkpoint_wrapper, logger)
    return validation_result

@hydra.main(config_path="configs", config_name="few_shot_spec_proof_plan_copra_proof", version_base="1.2")
def main(cfg):
    log_dir = cfg["log_dir"] if "log_dir" in cfg else "./.logs/eval_few_shot_spec_generation"
    exp_name = cfg["exp_name"] if "exp_name" in cfg else "eval_few_shot_spec_generation"
    checkpoint_dir = cfg["checkpoint_dir"] if "checkpoint_dir" in cfg else "./.logs/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_file = os.path.join(checkpoint_dir, f"{exp_name}.jsonl")
    checkpoint = CheckpointWrapper.from_file(checkpoint_file)
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(log_dir, timestr)
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logger(name=exp_name, log_file=os.path.join(log_dir, f"{exp_name}.log"))
    test_report_dir = os.path.join(log_dir, "test_report")
    os.makedirs(test_report_dir, exist_ok=True)
    task_type, hyper_params = parse_config(cfg)
    benchmark = Benchmark()
    benchmark.load_all()
    problem_view = ProblemViewTask(
        benchmark=benchmark,
        component=TaskComponent.SPEC_ISOMORPHISM 
        if task_type == TaskType.SPEC_ISOMORPHISM else TaskComponent.PROOF_GENERATION,
        report_dir=test_report_dir
    )
    if "proof_dump_file_path" in hyper_params:
        hyper_params["proof_dump_file_path"] = os.path.join(log_dir, hyper_params["proof_dump_file_path"])
    problems_to_solve = cfg["problems_to_solve"] if "problems_to_solve" in cfg else "*"
    timeout_in_secs = cfg["timeout_in_secs"] if "timeout_in_secs" in cfg else 600    
    k = cfg["k"] if "k" in cfg else 1
    if problems_to_solve == "*":
        problems_to_solve = [x.problem_id for x in benchmark.problems]
    else:
        valid_problem_id = set(x.problem_id for x in benchmark.problems)
        assert all(isinstance(x, int) for x in problems_to_solve), "problems_to_solve should be a list of integers"
        assert all(x >= 0 for x in problems_to_solve), "problems_to_solve should be a list of integers greater than or equal to 0"
        assert all(x in valid_problem_id for x in problems_to_solve), f"problems_to_solve should be a list of integers in {valid_problem_id}"
        problems_to_solve_set = set()
        ordered_problems_to_solve = []
        for problem_idx in problems_to_solve:
            if problem_idx in problems_to_solve_set:
                continue
            problems_to_solve_set.add(problem_idx)
            ordered_problems_to_solve.append(problem_idx)
        problems_to_solve = ordered_problems_to_solve
    compilation_timeout = 150*1000 # 150 seconds
    for attempt_idx in range(k):
        remotes = []
        for idx in problems_to_solve:
            if checkpoint.is_attempted_k_times(idx, attempt_idx + 1):
                logger.info(f"Problem {idx} already attempted {attempt_idx + 1} times. Skipping.")
                continue
            if checkpoint.was_solved(idx):
                logger.info(f"Problem {idx} was already solved in previous attempts. Skipping.")
                continue
            if task_type == TaskType.SPEC_ISOMORPHISM:
                logger.info(f"Problem {idx} was not solved. Attempting to solve SPEC_ISOMORPHISM problem.")
                validation_result_remote = eval_spec_generation.remote(
                    cfg=cfg,
                    idx=idx,
                    attempt_idx=attempt_idx,
                    problem_view=problem_view,
                    logging_dir=log_dir,
                    hyper_params=hyper_params,
                    timeout_in_secs=timeout_in_secs,
                    compilation_timeout=compilation_timeout,
                    checkpoint_actor=checkpoint.actor,
                    save_path=checkpoint.save_path
                )
            else:
                logger.info(f"Problem {idx} was not solved. Attempting to solve PROOF_GENERATION problem.")
                validation_result_remote = eval_impl_generation.remote(
                    cfg=cfg,
                    idx=idx,
                    attempt_idx=attempt_idx,
                    problem_view=problem_view,
                    logging_dir=log_dir,
                    hyper_params=hyper_params,
                    timeout_in_secs=timeout_in_secs,
                    compilation_timeout=compilation_timeout,
                    checkpoint_actor=checkpoint.actor,
                    save_path=checkpoint.save_path
                )
            remotes.append(validation_result_remote)
        validation_results: list[ValidationResult] = ray.get(remotes)
        # Dump stats for the results so far
        eval_execution_info = checkpoint.get_all()
        num_problems_proven = sum(1 for info in eval_execution_info if info.is_proven)
        num_problems_compiled = sum(1 for info in eval_execution_info if info.compiles)
        logger.info(f"Attempt {attempt_idx + 1} results:"
        f" {num_problems_proven} problems proven,"
        f" {num_problems_compiled} problems compiled.")
        # List of problems that were proven so far
        proven_problems = [info.problem_id for info in eval_execution_info if info.is_proven]
        logger.info(f"For attempt {attempt_idx + 1}, the following problems were proven:\n{proven_problems}")

if __name__ == "__main__":
    root_dir = f"{os.path.abspath(__file__).split('clever_prover')[-2]}"
    os.environ["PYTHONPATH"] = f"{root_dir}:{os.environ.get('PYTHONPATH', '')}"
    from filelock import FileLock
    import json
    os.makedirs(".log/locks", exist_ok=True)
    ray_was_started = False
    print("Starting run_proof_search Pid: ", os.getpid())
    with FileLock(".log/locks/ray.lock"):
        if os.path.exists(".log/ray/session_latest"):
            with open(".log/ray/session_latest", "r") as f:
                ray_session = f.read()
                ray_session = json.loads(ray_session)
            ray_address = ray_session["address"]
            ray.init(address=ray_address)
            print("Ray was already started")
        else:
            ray_session = ray.init(
                num_cpus=8, 
                object_store_memory=150*2**30, 
                _memory=150*2**30, 
                logging_level=logging.CRITICAL, 
                ignore_reinit_error=False, 
                log_to_driver=False, 
                configure_logging=False,
                _system_config={"metrics_report_interval_ms": 3*10**8})
            with open(".log/ray/session_latest", "w") as f:
                f.write(json.dumps(ray_session))
            ray_was_started = True
            print("Ray was started")
            print("Ray session: ", ray_session)
    main()