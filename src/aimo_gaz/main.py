import hydra
import os
from aimo_gaz.solver.solver_config import parse_solver_config, Solver
from aimo_gaz.scripts.eval import evaluate_on_benchmarks


def test_solver(solver: Solver):
    problem = "Find the value of x in the equation x + 100 = 200."
    while problem != "exit":
        ans = solver.solve(problem)
        print(ans)
        problem = input("Enter a math problem to solve: ")
    pass

@hydra.main(config_path="configs", config_name="vanilla_few_shot_solver_config")
def main(cfg):
    solver_config = parse_solver_config(cfg)
    solver = solver_config.get_solver()
    with solver:
        test_solver(solver)
        # Run benchmarking here
        root = os.environ.get("AIMO_GAZ_ROOT")
        data_dir = os.path.dirname(root)
        data_dir = os.path.dirname(data_dir)
        data_dir = os.path.join(data_dir, "data")
        evaluate_on_benchmarks("kaggle_train_10", os.path.join(data_dir, "kaggle_train_10.csv"), solver)

if __name__ == "__main__":
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.chdir(dirpath)
    main()