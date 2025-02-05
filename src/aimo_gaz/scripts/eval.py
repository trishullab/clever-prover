import json
import csv
import logging
import time
import math
import matplotlib.pyplot as plt
from enum import Enum
from itp_interface.rl.simple_proof_env import ProofExecutorCallback, ProofAction, ProofEnvReRankStrategy, ProofEnv
from aimo_gaz.solver.abs_solver_and_tool import Solver
from aimo_gaz.solver.test_solver import TestSolver
from aimo_gaz.utils import string_utils


def get_json_data(path: str):
    with open(path, "r") as f:
        data = json.load(f)
        return [x for x in data]

def get_csv_data(path: str):
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return [x for x in reader]


class ProblemType(Enum):
    FIND = "FIND"
    PROVE = "PROVE"

def evaluate(data, solver_cls = TestSolver, solver: Solver = None, logger: logging.Logger = None):
    logger = logger if logger is not None else logging.getLogger(__name__)
    solver = solver_cls() if solver is None else solver

    problem_type_statistics = {}
    category_statistics = {}
    total = 0
    correct = 0
    total_time_left = 9 * 60 * 60 - 1.5 * 650 # 600 is an upper bound on the startup time, as seen from kaggle test logs
    for exidx, ex in enumerate(data):
        start_timer = time.time()

        natural_statement = ex.get("natural_statement", ex.get("problem", ex.get("Question")))
        assert natural_statement is not None, f"Natural statement not found in example: {ex}"

        natural_solution = ex.get("natural_solution")
        numerical_answer = ex.get("numerical_answer", ex.get("answer", ex.get("Answer")))

        problem_type = ProblemType.FIND if natural_solution != "None." else ProblemType.PROVE
        has_numerical_answer = (numerical_answer != "None")

        category = ex.get("Tag")
        name = ex.get("name")

        lean4_project_folder = "../../data/test/lean4_proj/"
        theorem_file_path = lean4_project_folder + f"Lean4Proj/HarmonicTest/{name}.lean" # TODO: use file path join?
        with open(theorem_file_path, "r") as theorem_file:
            theorem_statement_raw = theorem_file.read()
        theorem_statement_lines = []
        for line in theorem_statement_raw.splitlines():
            if line and not line.isspace() and not line.startswith("import ") and not line.startswith("open ") and not line.startswith("--"):
                theorem_statement_lines.append(line)
        theorem_statement = "\n".join(theorem_statement_lines)
        
        solver_is_correct = False

        if problem_type == ProblemType.FIND: # TODO: maybe refactor to avoid separation of FIND and PROVE (since they both end up being PROVE anyways)
            assert natural_solution is not None, f"Natural solution not found in example: {ex}"

            if has_numerical_answer:
                numerical_answer = string_utils.parse_float(numerical_answer) # TODO: handle non-numerical answers
                if numerical_answer is None:
                    logger.error(f"ERROR: Numerical answer '{numerical_answer}' is not a float or fraction for row {exidx}")
                    continue

            solver_ans = solver.solve(natural_statement, theorem_statement, problem_type, None, name, time_allowed = total_time_left // (50 - total))

            if has_numerical_answer:
                solver_ans_float = string_utils.parse_float(solver_ans)
                if solver_ans_float is None:
                    logger.info(f"ERROR: Solver answer '{solver_ans}' is not a float or fraction.")
                    solver_is_correct = False
                else:
                    eps = 1e-6
                    solver_is_correct = (abs(solver_ans_float - numerical_answer) < eps)
            else:
                solver_is_correct = True
        else:
            proof_exec_callback = ProofExecutorCallback(
                project_folder=lean4_project_folder,
                file_path=theorem_file_path,
                language=ProofAction.Language.LEAN4,
                always_use_retrieval=False,
                keep_local_context=True
            )
            theorem_name = name
            always_retrieve_thms = False
            retrieval_strategy = ProofEnvReRankStrategy.NO_RE_RANK

            with ProofEnv(name, proof_exec_callback, theorem_name, retrieval_strategy=retrieval_strategy, max_proof_depth=10, always_retrieve_thms=always_retrieve_thms) as proof_env:
                solver.solve(natural_statement, theorem_statement, problem_type, proof_env, name, time_allowed = total_time_left // (50 - total))

                solver_is_correct = proof_env.done

        total += 1
        correct += solver_is_correct
        logger.info(f"Example {exidx}:")
        logger.info(f"Problem Statement:\n{natural_statement}")
        logger.info(f"Theorem Statement:\n{theorem_statement}")
        logger.info(f"Problem type: {problem_type}")
        if problem_type == ProblemType.FIND:
            logger.info(f"Solution: {natural_solution}")
            logger.info(f"Numerical answer: {numerical_answer}")
            logger.info(f"Solver answer: {solver_ans}")
        logger.info(f"Correct: {solver_is_correct}")

        problem_type_statistics.setdefault(problem_type, {"correct": 0, "total": 0})["total"] += 1
        problem_type_statistics[problem_type]["correct"] += solver_is_correct

        if category:
            category_statistics.setdefault(category, {"correct": 0, "total": 0})["total"] += 1
            category_statistics[category]["correct"] += solver_is_correct
        
        total_time_left -= math.ceil(time.time()-start_timer)

    return {
        "total": total,
        "correct": correct,
        "problem_type_statistics": problem_type_statistics,
        "category_statistics": category_statistics,
    }


def plot_category_statistics(category_statistics, time_str, benchmark):
    categories = list(category_statistics.keys())
    accuracies = [category_statistics[cat]["correct"] / category_statistics[cat]["total"] for cat in categories]

    # Plot the accuracies per category
    plt.bar(categories, accuracies)
    plt.title("Accuracy per category")

    # Tilt the x-axis labels
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Accuracy")

    # Give more margin on the bottom for text to fit
    plt.subplots_adjust(bottom=0.3)

    # Set y-limits to 0 to 1
    plt.ylim(0, 1)
    plt.savefig(f".logs/{time_str}/{benchmark}/category_statistics.png")
    plt.close()
    # plt.show()

def evaluate_on_benchmarks(benchmark, benchmark_ext, valid_path, solver, time_str = None, logger : logging.Logger = None):
    logger = logger if logger is not None else logging.getLogger(__name__)
    data = get_json_data(valid_path) if benchmark_ext == "json" else get_csv_data(valid_path)

    stats = evaluate(data, solver=solver, logger=logger)

    logger.info(f"Benchmark: {benchmark}")
    logger.info(f"Accuracy: {stats['correct']} / {stats['total']} = {stats['correct'] / stats['total']:.2f}")
    for problem_type, problem_type_stats in stats["problem_type_statistics"].items():
        logger.info(f"Problem type: {problem_type.value} ({problem_type_stats['correct']} / {problem_type_stats['total']} = {problem_type_stats['correct'] / problem_type_stats['total']:.2f})")
    for category, category_stats in stats["category_statistics"].items():
        logger.info(f"Category: {category} ({category_stats['correct']} / {category_stats['total']} = {category_stats['correct'] / category_stats['total']:.2f})")
    logger.info("\n\n")
    time_str = time.strftime("%Y%m%d-%H%M%S") if time_str is None else time_str
    if len(stats["category_statistics"]) != 0:
        plot_category_statistics(stats["category_statistics"], time_str, benchmark)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("--kaggle_train_10_path", type=str, default="../data/kaggle_train_10.csv")
    parser.add_argument("--valid_path", type=str, default="../data/valid.csv")

    parser.add_argument("--benchmarks", type=str, nargs="+", choices=["kaggle_train_10", "valid"])

    args = parser.parse_args()

    kaggle_train_10_path = args.kaggle_train_10_path
    benchmarks = args.benchmarks

    for benchmark in benchmarks:
        if benchmark == "kaggle_train_10":
            data = get_csv_data(kaggle_train_10_path)
        elif benchmark == "valid":
            data = get_csv_data(args.valid_path)
        else:
            assert False, f"Unknown benchmark: {benchmark}"

        stats = evaluate(data, solver_cls=TestSolver)

        print(f"Benchmark: {benchmark}")
        print(f"Accuracy: {stats['correct']} / {stats['total']} = {stats['correct'] / stats['total']:.2f}")
        for problem_type, problem_type_stats in stats["problem_type_statistics"].items():
            print(f"Problem type: {problem_type.value} ({problem_type_stats['correct']} / {problem_type_stats['total']} = {problem_type_stats['correct'] / problem_type_stats['total']:.2f})")
        for category, category_stats in stats["category_statistics"].items():
            print(f"Category: {category} ({category_stats['correct']} / {category_stats['total']} = {category_stats['correct'] / category_stats['total']:.2f})")
        print("\n\n")

        if len(stats["category_statistics"]) != 0:
            plot_category_statistics(stats["category_statistics"])
