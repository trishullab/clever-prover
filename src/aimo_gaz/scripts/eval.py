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
    FIND_NUMERICAL = "FIND_NUMERICAL"
    FIND_NONNUMERICAL = "FIND_NONNUMERICAL"
    PROVE = "PROVE"

class ProblemState(Enum):
    FINDING = "FINDING"
    PROVING = "PROVING"
    PROVING_AFTER_FINDING = "PROVING_AFTER_FINDING"

def evaluate(data, solver_cls = TestSolver, solver: Solver = None, logger: logging.Logger = None):
    logger = logger if logger is not None else logging.getLogger(__name__)
    solver = solver_cls() if solver is None else solver

    problem_type_statistics = {}
    category_statistics = {}
    proved = 0
    total = 0
    numerical_correct = 0
    numerical_total = 0
    total_time_left = 9 * 60 * 60 - 1.5 * 650 # 600 is an upper bound on the startup time, as seen from kaggle test logs
    for exidx, ex in enumerate(data):
        start_timer = time.time()

        logger.info("---Starting Problem---")

        natural_statement = ex.get("natural_statement", ex.get("problem", ex.get("Question")))
        assert natural_statement is not None, f"Natural statement not found in example: {ex}"

        natural_solution = ex.get("natural_solution")
        numerical_answer = ex.get("numerical_answer", ex.get("answer", ex.get("Answer")))

        if natural_solution != "None.":
            if numerical_answer != "None":
                problem_type = ProblemType.FIND_NUMERICAL
            else:
                problem_type = ProblemType.FIND_NONNUMERICAL
        else:
            problem_type = ProblemType.PROVE

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

        if problem_type == ProblemType.FIND_NUMERICAL or problem_type == ProblemType.FIND_NONNUMERICAL: # TODO: maybe refactor to avoid separation of FIND and PROVE (since they both end up being PROVE anyways)
            assert natural_solution is not None, f"Natural solution not found in example: {ex}"

            if problem_type == ProblemType.FIND_NUMERICAL:
                numerical_answer = string_utils.parse_float(numerical_answer)
                if numerical_answer is None:
                    logger.error(f"ERROR: Numerical answer '{numerical_answer}' is not a float or fraction for row {exidx}")
                    continue

            proof_env_done, solver_ans = solver.solve(natural_statement, theorem_statement, ProblemState.FINDING, None, name, time_allowed = total_time_left // (50 - total))

            if problem_type == ProblemType.FIND_NUMERICAL:
                solver_is_correct = False
                solver_ans_float = string_utils.parse_float(solver_ans)
                if solver_ans_float is None:
                    logger.info(f"ERROR: Solver answer '{solver_ans}' is not a float or fraction.")
                    solver_is_correct = False
                else:
                    eps = 1e-6
                    solver_is_correct = (abs(solver_ans_float - numerical_answer) < eps)
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
                proof_env_done, _ = solver.solve(natural_statement, theorem_statement, ProblemState.PROVING, proof_env, name, time_allowed = total_time_left // (50 - total))

        proved += int(proof_env_done) # TODO: maybe use actual proof_env.done in future
        total += 1
        if problem_type == ProblemType.FIND_NUMERICAL:
            numerical_correct += int(solver_is_correct)
            numerical_total += 1
        logger.info("---Problem Result---")
        logger.info(f"Example {exidx}:")
        logger.info(f"Problem Statement:\n{natural_statement}")
        logger.info(f"Theorem Statement:\n{theorem_statement}")
        logger.info(f"Problem Type: {problem_type}")
        logger.info(f"Proved: {proof_env_done}")
        if problem_type == ProblemType.FIND_NUMERICAL or problem_type == ProblemType.FIND_NONNUMERICAL:
            logger.info("---FIND Result---")
            logger.info(f"Solution: {natural_solution}")
            logger.info(f"Solver Answer: {solver_ans}")
            if problem_type == ProblemType.FIND_NUMERICAL:
                logger.info(f"Numerical Answer: {numerical_answer}")
                logger.info(f"Numerical Correct: {solver_is_correct}")

        problem_type_statistics.setdefault(problem_type, {"proved": 0, "total": 0})
        problem_type_statistics[problem_type]["proved"] += int(proof_env_done)
        problem_type_statistics[problem_type]["total"] += 1

        if category:
            category_statistics.setdefault(category, {"proved": 0, "total": 0})
            category_statistics[category]["proved"] += int(proof_env_done)
            category_statistics[category]["total"] += 1

        total_time_left -= math.ceil(time.time()-start_timer)

    return {
        "proved": proved,
        "total": total,
        "numerical_correct": numerical_correct,
        "numerical_total": numerical_total,
        "problem_type_statistics": problem_type_statistics,
        "category_statistics": category_statistics,
    }


def plot_category_statistics(category_statistics, time_str, benchmark):
    categories = list(category_statistics.keys())
    accuracies = [(category_statistics[cat]["proved"] / category_statistics[cat]["total"]) for cat in categories]

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

    logger.info("---Final Results---")
    logger.info(f"Benchmark: {benchmark}")
    logger.info(f"Prove Accuracy: {stats['proved']} / {stats['total']} = {stats['proved'] / stats['total']:.2f}")
    if stats["numerical_total"] > 0:
        logger.info(f"Numerical Accuracy: {stats['numerical_correct']} / {stats['numerical_total']} = {stats['numerical_correct'] / stats['numerical_total']:.2f}")
    for problem_type, problem_type_stats in stats["problem_type_statistics"].items():
        logger.info(f"Problem Type: {problem_type.value} ({problem_type_stats['proved']} / {problem_type_stats['total']} = {problem_type_stats['proved'] / problem_type_stats['total']:.2f})")
    for category, category_stats in stats["category_statistics"].items():
        logger.info(f"Category: {category} ({category_stats['proved']} / {category_stats['total']} = {category_stats['proved'] / category_stats['total']:.2f})")
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
        print(f"Prove Accuracy: {stats['proved']} / {stats['total']} = {stats['proved'] / stats['total']:.2f}")
        if stats["numerical_total"] > 0:
            print(f"Numerical Accuracy: {stats['numerical_correct']} / {stats['numerical_total']} = {stats['numerical_correct'] / stats['numerical_total']:.2f}")
        for problem_type, problem_type_stats in stats["problem_type_statistics"].items():
            print(f"Problem Type: {problem_type.value} ({problem_type_stats['proved']} / {problem_type_stats['total']} = {problem_type_stats['proved'] / problem_type_stats['total']:.2f})")
        for category, category_stats in stats["category_statistics"].items():
            print(f"Category: {category} ({category_stats['proved']} / {category_stats['total']} = {category_stats['proved'] / category_stats['total']:.2f})")
        print("\n\n")

        if len(stats["category_statistics"]) != 0:
            plot_category_statistics(stats["category_statistics"])
