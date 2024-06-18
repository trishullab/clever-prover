import csv
import matplotlib.pyplot as plt

from aimo_gaz.solver.abs_solver import Solver
from aimo_gaz.solver.test_solver import TestSolver


def get_csv_data(path: str):
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return [x for x in reader]


def evaluate(data, solver_cls = TestSolver):
    solver = solver_cls()

    category_statistics = {}
    total = 0
    correct = 0

    for exidx, ex in enumerate(data):
        problem = ex.get('problem', ex.get('Question'))
        assert problem is not None, f'Problem not found in example: {ex}'

        answer = ex.get('answer', ex.get('Answer'))
        assert answer is not None, f'Answer not found in example: {ex}'

        try:
            answer = int(answer)
        except ValueError:
            print("ERROR: Answer is not an integer for row {}".format(exidx))
            continue

        category = ex.get('Tag')

        solver_ans = solver.solve(problem)

        solver_is_correct = int(solver_ans) % 1000 == int(answer)

        total += 1
        correct += solver_is_correct

        if category:
            category_statistics.setdefault(category, {'correct': 0, 'total': 0})['total'] += 1
            category_statistics[category]['correct'] += correct

    return {
        'total': total,
        'correct': correct,
        'category_statistics': category_statistics,
    }


def plot_category_statistics(category_statistics):

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

    plt.show()


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

        # TODO - you can change the solver class when more are made.
        stats = evaluate(data, solver_cls=TestSolver)

        print(f'Benchmark: {benchmark}')
        print(f'Accuracy: {stats["correct"] / stats["total"]:.2f}')
        for category, category_stats in stats['category_statistics'].items():
            print(f'Category: {category} ({category_stats["correct"] / category_stats["total"]:.2f})')
        print('\n\n')

        if len(stats['category_statistics']) != 0:
            plot_category_statistics(stats['category_statistics'])

