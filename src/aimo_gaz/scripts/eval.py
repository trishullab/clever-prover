import csv
import logging
import time
import matplotlib.pyplot as plt
import math
from aimo_gaz.solver.abs_solver_and_tool import Solver
from aimo_gaz.solver.test_solver import TestSolver
from aimo_gaz.solver.vanilla_few_shot_solver import FewShotSolver


def get_csv_data(path: str):
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return [x for x in reader]


def evaluate(data, solver_cls = TestSolver, solver: Solver = None, logger : logging.Logger = None):
    logger = logger if logger is not None else logging.getLogger(__name__)
    solver = solver_cls() if solver is None else solver

    category_statistics = {}
    total = 0
    correct = 0
    total_time_left = 9 * 60 * 60 - 1.5 * 650 # 600 is an upper bound on the startup time, as seen from kaggle test logs
    for exidx, ex in enumerate(data):
        start_timer = time.time()
        problem = ex.get('problem', ex.get('Question'))
        assert problem is not None, f'Problem not found in example: {ex}'

        answer = ex.get('answer', ex.get('Answer'))
        assert answer is not None, f'Answer not found in example: {ex}'

        try:
            answer = float(answer)
        except ValueError:
            pass
        if not isinstance(answer, float):
            try:
                answer = eval(answer)
            except:
                pass
        if not isinstance(answer, float):
            logger.error(f"ERROR: Answer '{answer}' is not a float or fraction for row {exidx}")
            continue

        category = ex.get('Tag')

        solver_ans = solver.solve(problem, time_allowed = total_time_left//(50 - total))

        # solver_is_correct = int(solver_ans) % 1000 == int(answer)
        eps = 1e-6
        solver_is_correct = (abs(solver_ans - answer) < eps)

        total += 1
        correct += solver_is_correct
        logger.info(f'Example {exidx}:')
        logger.info(f'Problem: {problem}')
        logger.info(f'Answer: {answer}')
        logger.info(f'Solver answer: {solver_ans}')
        logger.info(f'Correct: {solver_is_correct}')

        if category:
            category_statistics.setdefault(category, {'correct': 0, 'total': 0})['total'] += 1
            category_statistics[category]['correct'] += solver_is_correct
        total_time_left -= math.ceil(time.time()-start_timer)
    return {
        'total': total,
        'correct': correct,
        'category_statistics': category_statistics,
    }


def plot_category_statistics(category_statistics, time_str, benchmark):

    categories = list(category_statistics.keys())
    accuracies = [category_statistics[cat]['correct'] / category_statistics[cat]['total'] for cat in categories]

    # Plot the accuracies per category
    plt.bar(categories, accuracies)
    plt.title('Accuracy per category')

    # Tilt the x-axis labels
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Accuracy')

    # Give more margin on the bottom for text to fit
    plt.subplots_adjust(bottom=0.3)

    # Set y-limits to 0 to 1
    plt.ylim(0, 1)
    plt.savefig(f'.logs/{time_str}/{benchmark}/category_statistics.png')
    plt.close()
    # plt.show()

def evaluate_on_benchmarks(benchmark, valid_path, solver, time_str = None, logger : logging.Logger = None):
    logger = logger if logger is not None else logging.getLogger(__name__)
    data = get_csv_data(valid_path)

    stats = evaluate(data, solver=solver, logger=logger)

    logger.info(f'Benchmark: {benchmark}')
    logger.info(f'Accuracy: {stats["correct"] / stats["total"]:.2f} ({stats["correct"]} / {stats["total"]})')
    for category, category_stats in stats['category_statistics'].items():
        logger.info(f'Category: {category} ({category_stats["correct"] / category_stats["total"]:.2f} ({category_stats["correct"]} / {category_stats["total"]}))')
    logger.info('\n\n')
    time_str = time.strftime("%Y%m%d-%H%M%S") if time_str is None else time_str
    if len(stats['category_statistics']) != 0:
        plot_category_statistics(stats['category_statistics'], time_str, benchmark)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('--kaggle_train_10_path', type=str, default='../data/kaggle_train_10.csv')
    parser.add_argument('--valid_path', type=str, default='../data/valid.csv')

    parser.add_argument('--benchmarks', type=str, nargs='+', choices=['kaggle_train_10', 'valid'])

    args = parser.parse_args()

    kaggle_train_10_path = args.kaggle_train_10_path
    benchmarks = args.benchmarks

    for benchmark in benchmarks:
        if benchmark == 'kaggle_train_10':
            data = get_csv_data(kaggle_train_10_path)
        elif benchmark == 'valid':
            data = get_csv_data(args.valid_path)
        else:
            assert False, f'Unknown benchmark: {benchmark}'

        # TODO: - you can change the solver class when more are made.
        stats = evaluate(data, solver_cls=TestSolver)

        print(f'Benchmark: {benchmark}')
        print(f'Accuracy: {stats["correct"] / stats["total"]:.2f} ({stats["correct"]} / {stats["total"]})')
        for category, category_stats in stats['category_statistics'].items():
            print(f'Category: {category} ({category_stats["correct"] / category_stats["total"]:.2f} ({category_stats["correct"]} / {category_stats["total"]}))')
        print('\n\n')

        if len(stats['category_statistics']) != 0:
            plot_category_statistics(stats['category_statistics'])
