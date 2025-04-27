from evaluator.evaluator import evaluate_pddl

def run_evaluation(gt, pred, check_solvable = True):
    return evaluate_pddl(gt, pred, check_solvable)