import hydra
import os
import time
from aimo_gaz.solver.solver_and_tool_config import parse_solver_or_tool_config, Solver
from aimo_gaz.scripts.eval import evaluate_on_benchmarks
from aimo_gaz.utils.log_utils import setup_logger


def test_solver(solver: Solver):
    problem = "Find the value of x in the equation x + 100 = 200."
    while problem != "exit":
        ans = solver.solve(problem)
        print(ans)
        problem = input("Enter a math problem to solve: ")
    pass

# @hydra.main(config_path="configs", config_name="coordination_solver_config_pceelmv", version_base="1.2")
@hydra.main(config_path="configs", config_name="coordination_solver_config_cthl", version_base="1.2")
def main(cfg):
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.environ["USE_VLLM"] = "True"
    os.chdir(dirpath)
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)
    logger = setup_logger("aimo_gaz", f".logs/{time_str}/aimo_gaz.log")
    solver_config = parse_solver_or_tool_config(cfg)
    solver = solver_config.get_solver_or_tool(logger)
    with solver:
        # test_solver(solver)
        # Run benchmarking here
        root = os.environ.get("AIMO_GAZ_ROOT")
        data_dir = os.path.dirname(root)
        data_dir = os.path.dirname(data_dir)
        data_dir = os.path.join(data_dir, "data")
        # benchmark = "valid"
        benchmark = "kaggle_train_1"
        # benchmark = "kaggle_train_1_x_20_temp"
        # benchmark = "harmonic_find_test_28"
        logger.info(f"Running on {benchmark}")
        os.makedirs(f".logs/{time_str}/{benchmark}", exist_ok=True)
        evaluate_on_benchmarks(benchmark, os.path.join(data_dir, f"{benchmark}.csv"), solver, time_str, logger)

if __name__ == "__main__":
    main()
