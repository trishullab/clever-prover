import hydra
import os
import time
from aimo_gaz.solver.solver_and_tool_config import parse_solver_or_tool_config, Solver
from aimo_gaz.scripts.eval import evaluate_on_benchmarks
from aimo_gaz.utils.log_utils import setup_logger
import torch.distributed as dist
import pandas as pd
import numpy as np
import torch

def split_csv(file_path, num_splits, data_dir):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Calculate the number of rows per split
    num_rows = len(df)
    rows_per_split = int(np.ceil(num_rows / num_splits))
    
    # Split and save each chunk as a separate CSV file
    for i in range(num_splits):
        start_row = i * rows_per_split
        end_row = min((i + 1) * rows_per_split, num_rows)
        chunk = df.iloc[start_row:end_row]
        
        output_file = os.path.join(data_dir, f'split_{i}.csv')
        chunk.to_csv(output_file, index=False)
        print(f'Saved {output_file}')

def attempt_on_subset(rank, size, time_str, cfg, csv_path, benchmark_name, config_name="coordination_solver_config", version_base="1.2"):
    dist.init_process_group(backend='nccl', rank=rank, world_size=size)
    logger = setup_logger("aimo_gaz", f".logs/{time_str}/aimo_gaz_{rank}.log")
    solver_config = parse_solver_or_tool_config(cfg)
    solver = solver_config.get_solver_or_tool(logger)
    with solver:
        logger.info(f"Running on {benchmark_name} split {rank}.")
        os.makedirs(f".logs/{time_str}/{benchmark_name}", exist_ok=True)
        evaluate_on_benchmarks(benchmark_name, csv_path, solver, time_str, logger)
    dist.destroy_process_group()

@hydra.main(config_path="configs", config_name="coordination_solver_config", version_base="1.2")
def main(cfg):
    dist.init_process_group(backend='nccl')
    dirpath = os.path.dirname(os.path.abspath(__file__))
    os.environ["AIMO_GAZ_ROOT"] = dirpath
    os.chdir(dirpath)
    time_str = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    os.makedirs(f".logs/{time_str}", exist_ok=True)

    # world_size = dist.get_world_size() or 1
    size = torch.cuda.device_count()
    # assert size == world_size
    rank = dist.get_rank() or 0

    # split csv into several pieces
    root = os.environ.get("AIMO_GAZ_ROOT")
    data_dir = os.path.dirname(root)
    data_dir = os.path.dirname(data_dir)
    data_dir = os.path.join(data_dir, "data")
    os.makedirs(os.path.join(data_dir, "temp"))
    split_csv(os.path.join(data_dir, "kaggle_train_10.csv"), size, os.path.join(data_dir, "temp"))

    processes = []
    for rank in range(size):
        csv_file = f'output_splits/split_{rank}.csv'
        p = torch.multiprocessing.Process(target=attempt_on_subset, args=(rank, size, time_str, cfg, csv_file, "kaggle_train_10"))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()