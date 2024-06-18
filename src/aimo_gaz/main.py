import hydra
import os
from aimo_gaz.solver.solver_config import parse_solver_config, Solver


def test_solver(solver: Solver):
    ans = solver.solve("Find the value of x in the equation x + 100 = 200.[END]")
    print(ans)  # Should print 100
    pass

@hydra.main(config_path="configs", config_name="vanilla_few_shot_solver_config")
def main(cfg):
    solver_config = parse_solver_config(cfg)
    solver = solver_config.get_solver()
    with solver:
        test_solver(solver)

if __name__ == "__main__":
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.chdir(dirpath)
    main()