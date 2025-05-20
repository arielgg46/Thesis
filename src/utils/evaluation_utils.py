import os
import planetarium

from utils.planning_utils import generate_plan
from utils.io_utils import save_text
from domains.utils import get_domain_path

from typing import Tuple

def evaluate_pddl(domain, pddl_gt, pddl_pred, is_placeholder) -> Tuple[bool, bool, bool]:
    if domain in ["blocksworld", "gripper"]: # The ones with custom planners
        parseable, solvable, correct = planetarium.evaluate(source_pddl_str = pddl_gt, target_pddl_str = pddl_pred, check_solveable = True, is_placeholder = is_placeholder)
    else:
        parseable, solvable, correct = planetarium.evaluate(source_pddl_str = pddl_gt, target_pddl_str = pddl_pred, check_solveable = False, is_placeholder = is_placeholder)

        if not parseable:
            return False, False, False
        
        domain_path = get_domain_path(domain)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        pddl_pred_path = os.path.join(BASE_DIR, "pddl_pred.pddl")
        save_text(pddl_pred_path, pddl_pred)

        plan = generate_plan(domain_path, pddl_pred_path)
        if plan is None:
            solvable = False
        else:
            solvable = True

    return parseable, solvable, correct