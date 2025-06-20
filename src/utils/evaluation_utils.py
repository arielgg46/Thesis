import os, re
import planetarium
from typing import List

import numpy as np
from utils.pddl_utils import extract_typed_objects, split_pddl_problem_sections
from utils.planning_utils import generate_plan
from utils.io_utils import save_text
from domains.utils import get_domain_path

from typing import Tuple

def evaluate_pddl(domain, pddl_gt, pddl_pred, is_placeholder) -> Tuple[bool, bool, bool]:
    try:
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
    except Exception as e:
        print(e)
        return False, False, False
    return parseable, solvable, correct

def compare_objects(objects_gt: dict, objects_pred: dict) -> List[str]:
    feedback = []

    for type in objects_gt:
        cardinality_gt = len(objects_gt[type])
        if type in objects_pred:
            cardinality_pred = len(objects_pred[type])
            if cardinality_pred != cardinality_gt:
                feedback.append(f'There are {cardinality_pred} objects of type "{type}", there should be {cardinality_gt}.')
        else:
            if cardinality_gt > 0:
                feedback.append(f'The type "{type}" is not present in the generated objects. There should be {cardinality_gt} objects of this type.')
    
    for type in objects_pred:
        if type not in objects_gt:
            feedback.append(f'There should be no objects of type "{type}".')

    return feedback

def eval_trial(task: dict, modeling_agent_resp):
    domain = task["domain"]
    pddl_gt = task["problem_pddl"]
    pddl_pred = modeling_agent_resp["problem_pddl"]
    is_placeholder = task["is_placeholder"]

    parseable, solvable, correct = evaluate_pddl(domain, pddl_gt, pddl_pred, is_placeholder)
    
    init2_solvable = goal2_solvable = solvable
    init2_correct = goal2_correct = correct

    feedback = []
    if not parseable:
        feedback.append("The generated PDDL is not parseable, indicating it contains syntax errors or references to undefined objects.") # if using GCD it can only be truncated
    
    objects_gt = extract_typed_objects(pddl_gt)
    objects_pred_pddl = extract_typed_objects(pddl_pred)
    objects_count_ok = True

    if len(objects_pred_pddl) == 0:
        feedback.append("The problem PDDL lacks an object declaration block.")
        objects_count_ok = False
    else:
        # Only available in training
        objects_feedback = compare_objects(objects_gt, objects_pred_pddl)
        if len(objects_feedback) > 0:
            objects_count_ok = False

        for fb in objects_feedback:
            feedback.append(fb)
    
    # if "objects" in modeling_agent_resp: 
        # objects_pred = modeling_agent_resp["objects"]
        # print(objects_pred)
        # print(objects_pred_pddl)
        # if objects_pred_pddl != objects_pred:
        #     raise ValueError("Objects differ between extraction phase and generated PDDL.")
    

    if parseable and not solvable:
        prefix, init_content, middle, goal_content, suffix = split_pddl_problem_sections(pddl_pred)
        init2_pddl = prefix + init_content + middle + init_content + suffix
        goal2_pddl = prefix + goal_content + middle + goal_content + suffix
        
        init2_parseable, init2_solvable, init2_correct = evaluate_pddl(domain, init2_pddl, init2_pddl, is_placeholder)
        goal2_parseable, goal2_solvable, goal2_correct = evaluate_pddl(domain, goal2_pddl, goal2_pddl, is_placeholder)

        print(init2_correct, goal2_correct)
        if not init2_solvable and not goal2_solvable:
            feedback.append("The generated PDDL is parseable but unsolvable: both the initial and goal states are internally inconsistent, each contains conflicting predicates.")
        elif not init2_solvable and goal2_solvable:
            feedback.append("The generated PDDL is parseable but unsolvable: the goal state does not contain conflicting predicates, but the initial state does, it is internally inconsistent.")
        elif init2_solvable and not goal2_solvable:
            feedback.append("The generated PDDL is parseable but unsolvable: the initial state does not contain conflicting predicates, but the goal state does, it is internally inconsistent.")
        else:
            feedback.append("The generated PDDL is parseable but unsolvable: no valid sequence of actions leads from the initial to the goal state, one or both states could contain conflicting predicates.")
    
    # Only available in training
    if parseable and solvable and not correct:
        feedback_preffix = "The generated PDDL is parseable and solvable, but semantically incorrect with respect to the problem description (may only be lack of full specificity)."
        prefix_pred, init_content_pred, middle_pred, goal_content_pred, suffix_pred = split_pddl_problem_sections(pddl_pred)
        prefix_gt, init_content_gt, middle_gt, goal_content_gt, suffix_gt = split_pddl_problem_sections(pddl_gt)
        
        init2_pddl_pred = prefix_pred + init_content_pred + middle_pred + init_content_pred + suffix_pred
        goal2_pddl_pred = prefix_pred + goal_content_pred + middle_pred + goal_content_pred + suffix_pred
          
        and_match = re.search(r'and', middle_gt[:])
        if not and_match:
            middle_gt += " (and\n"
            suffix_gt += ")"
        init2_pddl_gt = prefix_gt + init_content_gt + middle_gt + init_content_gt + suffix_gt
        goal2_pddl_gt = prefix_gt + goal_content_gt + middle_gt + goal_content_gt + suffix_gt


        # print(prefix_gt)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(goal_content_gt)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(middle_gt)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(goal_content_gt)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(suffix_gt)
        # print("-------------")
        # print(init2_pddl_gt)
        # print()
        # print()

        # print(prefix_pred)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(goal_content_pred)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(middle_pred)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(goal_content_pred)
        # print("-------------")
        # print()
        # print()
        # print("-------------")
        # print(suffix_pred)
        # print("-------------")
        # print(init2_pddl_pred)
        # print()
        # print()
        # return

        _, _, init2_correct = evaluate_pddl(domain, init2_pddl_gt, init2_pddl_pred, is_placeholder)
        _, _, goal2_correct = evaluate_pddl(domain, goal2_pddl_gt, goal2_pddl_pred, is_placeholder)
        if not init2_correct and not goal2_correct:
            feedback.append(feedback_preffix + "Both the initial and goal states are semantically incorrect: they do not faithfully represent the natural language problem.")
        elif not init2_correct and goal2_correct:
            feedback.append(feedback_preffix + "The initial state is semantically incorrect, while the goal state aligns with the natural language description of the problem.")
        elif init2_correct and not goal2_correct:
            feedback.append(feedback_preffix + "The initial state is semantically correct, but the goal state does not align with the natural language description of the problem.")
        else:
            feedback.append(feedback_preffix + "The combination of initial and goal states doesn't faithfully represent the natural language problem")

    if parseable and solvable and correct:
        feedback.append("Nothing to fix, the generated PDDL is parseable, solvable and semantically correct.")

    return {
        "objects_count_ok": objects_count_ok,
        "parseable": parseable,
        
        "solvable": solvable,
        "init2_solvable": init2_solvable,
        "goal2_solvable": goal2_solvable,

        "correct": correct,
        "init2_correct": init2_correct,
        "goal2_correct": goal2_correct,

        "feedback": feedback
    }

def bootstrapping(resultados):
    # Resultados binarios de un agente para una métrica (por ejemplo, "Correct")
    # (Supón que ya los cargaste de tu CSV o archivo)
    resultados = np.array(resultados)

    # Número de iteraciones bootstrap
    N = 100000
    np.random.seed(42)
    bootstrap_vals = np.random.choice(resultados, size=(N, len(resultados)), replace=True)
    metricas = bootstrap_vals.mean(axis=1)

    # Calcular media y percentiles
    media = resultados.mean()
    ic_95 = np.percentile(metricas, [2.5, 97.5])

    # print(f"Porcentaje promedio: {media*100:.2f} %")
    # print(f"IC 95%: [{ic_95[0]*100:.2f} %, {ic_95[1]*100:.2f} %]")
    return ic_95

# pddl_gt = """(define (problem grid_to_all_different_1_6_6)
#     (:domain floor-tile)
#     (:requirements :typing)
#     (:objects color1 color2 color3 color4 color5 color6 - color robot1 - robot tile1 tile2 tile3 tile4 tile5 tile6 - tile)
#     (:init (available-color color1) (available-color color2) (available-color color3) (available-color color4) (available-color color5) (available-color color6) (right tile2 tile1) (right tile4 tile3) (right tile6 tile5) (robot-at robot1 tile1) (robot-has robot1 color1) (up tile1 tile3) (up tile2 tile4) (up tile3 tile5) (up tile4 tile6))
#     (:goal (and (painted tile1 color1) (painted tile2 color2) (painted tile3 color3) (painted tile4 color4) (painted tile5 color5) (painted tile6 color6)))
# )"""

# pddl_pred = """(define (problem grid_to_all_different_1_6_6)
#     (:domain floor-tile)
#     (:requirements :typing)
#     (:objects color1 color2 color3 color4 color5 color6 - color robot1 - robot tile1 tile2 tile3 tile4 tile5 tile6 - tile)
#     (:init (available-color color1) (available-color color2) (available-color color3) (available-color color4) (available-color color5) (available-color color6) (right tile2 tile1) (right tile4 tile3) (right tile6 tile5) (robot-at robot1 tile1) (robot-has robot1 color1) (up tile1 tile3) (up tile2 tile4) (up tile3 tile5) (up tile4 tile6))
#     (:goal (and (painted tile1 color1) (painted tile2 color2) (painted tile3 color3) (painted tile4 color4) (painted tile5 color5) (painted tile6 color6)))
# )"""


# task = {
#     "domain": "floor-tile",
#     "problem_pddl": pddl_gt
# }

# modeling_agent_resp = {
#     "problem_pddl": pddl_pred,
#     "objects": extract_typed_objects(pddl_pred)
# }

# fb = eval_trial(task, modeling_agent_resp)

# print(fb)