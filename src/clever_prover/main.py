import hydra
import os
import time
from clever_prover.solver.solver_and_tool_config import parse_solver_or_tool_config, Solver
from clever_prover.scripts.eval import evaluate_on_benchmarks
from clever_prover.utils.log_utils import setup_logger


def test_solver(solver: Solver):
    problem = "Find the value of x in the equation x + 100 = 200."
    while problem != "exit":
        ans = solver.solve(problem)
        print(ans)
        problem = input("Enter a math problem to solve: ")

@hydra.main(config_path="configs/", config_name="coordination_solver_config_pippc", version_base="1.2")
def main(cfg):
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["CLEVER_PROVER_ROOT"] = dirpath
    os.environ["USE_VLLM"] = "True"
    os.chdir(dirpath)
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    logger = setup_logger("clever_prover", f".logs/{time_str}/clever_prover.log")
    coordinator_history_logger = setup_logger("clever_prover_coordinator_history", f".logs/{time_str}/clever_prover_coordinator_history.log")
    solver_config = parse_solver_or_tool_config(cfg)
    solver = solver_config.get_solver_or_tool(logger, coordinator_history_logger) # TODO: second logger only works with coordination solver
    with solver:
        # test_solver(solver)
        # Run benchmarking here
        root = os.environ.get("CLEVER_PROVER_ROOT")
        data_dir = os.path.dirname(root)
        data_dir = os.path.dirname(data_dir)
        data_dir = os.path.join(data_dir, "data")
        # benchmark = "problem_2_1"
        # benchmark = "simple_problems_2"
        benchmark = "random_problems_10"
        # benchmark_ext = "csv"
        benchmark_ext = "json"
        logger.info("---Starting Run---")
        logger.info(f"Running on {benchmark}")
        os.makedirs(f".logs/{time_str}/{benchmark}", exist_ok=True)
        evaluate_on_benchmarks(benchmark, benchmark_ext, os.path.join(data_dir, f"{benchmark}.{benchmark_ext}"), solver, time_str, logger)

if __name__ == "__main__":
    main()
