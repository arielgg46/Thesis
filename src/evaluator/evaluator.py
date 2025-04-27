import planetarium

def evaluate_pddl(gt: str, pred: str, check_solvable: bool) -> tuple[bool, bool, bool]:
    return planetarium.evaluate(gt, pred, check_solveable=check_solvable)
