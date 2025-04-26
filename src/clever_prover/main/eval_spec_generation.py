#!/usr/bin/env python3

import hydra
import os
import time
import asyncio
from clever_bench.task import ProblemViewTask, TaskComponent, ValidationResult
from clever_bench.benchmark import Benchmark
from clever_prover.main.parse_config import parse_config, parse_spec_generation_class
from itp_interface.tools.log_utils import setup_logger

@hydra.main(config_path="configs", config_name="few_shot_spec_generation", version_base="1.2")
def main(cfg):
    log_dir = cfg["log_dir"] if "log_dir" in cfg else "./.logs/eval_few_shot_spec_generation"
    exp_name = cfg["exp_name"] if "exp_name" in cfg else "eval_few_shot_spec_generation"
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(log_dir, timestr)
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logger(name=exp_name, log_file=os.path.join(log_dir, f"{exp_name}.log"))
    test_report_dir = os.path.join(log_dir, "test_report")
    os.makedirs(test_report_dir, exist_ok=True)
    benchmark = Benchmark()
    benchmark.load_all()
    problem_view = ProblemViewTask(
        benchmark=benchmark,
        component=TaskComponent.SPEC_ISOMORPHISM,
        report_dir=test_report_dir
    )
    hyper_params = parse_config(cfg)
    if "proof_dump_file_path" in hyper_params:
        hyper_params["proof_dump_file_path"] = os.path.join(log_dir, hyper_params["proof_dump_file_path"])
    problems_to_solve = cfg["problems_to_solve"] if "problems_to_solve" in cfg else "*"
    timeout_in_secs = cfg["timeout_in_secs"] if "timeout_in_secs" in cfg else 600    
    k = cfg["k"] if "k" in cfg else 1
    if problems_to_solve == "*":
        problems_to_solve = list(range(len(benchmark.problems)))
    else:
        assert all(isinstance(x, int) for x in problems_to_solve), "problems_to_solve should be a list of integers"
        assert all(x < len(benchmark.problems) for x in problems_to_solve), "problems_to_solve should be a list of integers less than the number of problems"
        assert all(x >= 0 for x in problems_to_solve), "problems_to_solve should be a list of integers greater than or equal to 0"
        problems_to_solve = list(set(problems_to_solve))
    validation_results : dict[int, ValidationResult] = {}
    problem_solved_map: dict[int, int] = {}
    generated_compilable: dict[int, bool] = {}
    compilation_timeout = 150*1000 # 150 seconds
    for attempt_idx in range(1, k + 1):
        for idx in problems_to_solve:
            if idx in problem_solved_map:
                logger.info(f"Problem {idx} already solved in attempt {problem_solved_map[idx]}. Skipping.")
                continue
            spec_generation_strategy = parse_spec_generation_class(cfg)
            spec_generation_task = spec_generation_strategy(
                problem_id=idx,
                problem_view=problem_view,
                logger=logger,
                **hyper_params)
            _ = spec_generation_task.generate_specification(timeout_in_ms=timeout_in_secs * 1000, logger=logger)
            validation_result = asyncio.run(
                problem_view.submit_async(
                    problem=spec_generation_task.generated_spec_problem_view,
                    timeout_in_ms=compilation_timeout
                ))
            logger.info(f"Validation Result [{idx}] [compilation_ok]: {validation_result.compilation_ok}")
            validation_results[idx] = validation_result
            if validation_result.compilation_ok:
                logger.info(f"Problem {idx} was compiled successfully.")
                generated_compilable[idx] = True
            else:
                logger.error("Spec Generation failed.")
                logger.error(f"Spec Compilation Error: {validation_result.error_message[-300:]}")
                continue
                # No point in even attempting the proof if the spec generation failed
            _ = spec_generation_task.generate_spec_isomorphism_proof(timeout_in_ms=timeout_in_secs * 1000, logger=logger)
            # Submit the proof to the problem view
            validation_result = asyncio.run(
                problem_view.submit_async(
                    problem=spec_generation_task.generated_proof_problem_view,
                    timeout_in_ms=compilation_timeout
                ))
            logger.info(f"Validation Result [{idx}] [isomorphism_ok]: {validation_result.isomorphism_ok}")
            if not validation_result.compilation_ok:
                logger.error("Proof failed.")
                logger.error(f"Proof error: {validation_result.error_message[-300:]}")
            validation_result = validation_result
            if validation_result.isomorphism_ok:
                logger.info(f"Problem {idx} was solved successfully.")
                problem_solved_map[idx] = attempt_idx
            validation_results[idx] = validation_result
    for idx, _ in generated_compilable.items():
        if idx not in problem_solved_map:
            logger.info(f"Problem {idx} was not solved successfully, but was compilable.")
    for idx, validation_result in validation_results.items():
        if idx not in problem_solved_map and idx not in generated_compilable:
            logger.info(f"Problem {idx} was not solved successfully, and was not compilable.")
    for idx, attempt_idx in problem_solved_map.items():
        logger.info(f"Problem {idx} was solved successfully in attempt {attempt_idx}.")
    logger.info(f"Total problems solved: {len(problem_solved_map)}")
    logger.info(f"Total problems compilable: {len(generated_compilable)}")
    logger.info(f"Total problems not solved: {len(validation_results) - len(problem_solved_map)}")
    logger.info(f"Total problems not compilable: {len(validation_results) - len(generated_compilable)}")
    logger.info(f"Total problems: {len(validation_results)}")

if __name__ == "__main__":
    main()



