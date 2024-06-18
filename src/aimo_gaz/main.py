import hydra
import os
from aimo_gaz.solver.solver_config import parse_solver_config


def test_solver(solver):
    pass

@hydra.main(config_path="configs", config_name="test_solver_config")
def main(cfg):
    solver_config = parse_solver_config(cfg)
    solver = solver_config.get_solver()
    test_solver(solver)

if __name__ == "__main__":
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.chdir(dirpath)
    main()