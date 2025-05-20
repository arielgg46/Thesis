from typing import List

from utils.pddl_utils import extract_typed_objects, split_pddl_problem_sections
from utils.evaluation_utils import evaluate_pddl

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
    
    feedback = []
    if not parseable:
        feedback.append("The generated PDDL is not parseable.") # can only be truncated if using GCD
    
    objects_gt = extract_typed_objects(pddl_gt)
    objects_pred_pddl = extract_typed_objects(pddl_pred)

    if len(objects_pred_pddl) == 0:
        feedback.append("There is no objects declaration.")
    else:
        # Only available in training
        objects_feedback = compare_objects(objects_gt, objects_pred_pddl)
        objects_feedback_preffix = ""
        # objects_feedback_preffix = "Objects: "
        for fb in objects_feedback:
            feedback.append(objects_feedback_preffix + fb)
    
    # if "objects" in modeling_agent_resp: 
    #     objects_pred = modeling_agent_resp["objects"]
        # print(objects_pred)
        # print(objects_pred_pddl)
        # if objects_pred_pddl != objects_pred:
        #     raise ValueError("Objects differ between extraction phase and generated PDDL.")
    
    if parseable and not solvable:
        prefix, init_content, middle, goal_content, suffix = split_pddl_problem_sections(pddl_pred)
        init2_pddl = prefix + init_content + middle + init_content + suffix
        goal2_pddl = prefix + goal_content + middle + goal_content + suffix
        init2_parseable, init2_solvable, _ = evaluate_pddl(domain, init2_pddl, init2_pddl, is_placeholder)
        goal2_parseable, goal2_solvable, _ = evaluate_pddl(domain, goal2_pddl, goal2_pddl, is_placeholder)
        # print(init2_pddl)
        # print(goal2_pddl)
        # print(init2_parseable, init2_solvable)
        # print(goal2_parseable, goal2_solvable)
        feedback.append("The generated PDDL is not solvable, no plan can be found from initial to goal states.")
        if not init2_parseable:
            raise ValueError("PDDL with doubled init not parseable.")
        if not goal2_parseable:
            raise ValueError("PDDL with doubled goal not parseable.")
        if not init2_solvable:
            feedback.append("The initial state is invalid.") # contains conflicting or misused predicates
        if not goal2_solvable:
            feedback.append("The goal state is invalid.") # contains conflicting or misused predicates
    
    # Only available in training
    if parseable and solvable and not correct:
        feedback.append("The generated PDDL is parseable and solvable, but incorrect.") # not fully specified or not aligned with the given description of the problem
        prefix_pred, init_content_pred, middle_pred, goal_content_pred, suffix_pred = split_pddl_problem_sections(pddl_pred)
        prefix_gt, init_content_gt, middle_gt, goal_content_gt, suffix_gt = split_pddl_problem_sections(pddl_gt)
        
        init2_pddl_pred = prefix_pred + init_content_pred + middle_pred + init_content_pred + suffix_pred
        goal2_pddl_pred = prefix_pred + goal_content_pred + middle_pred + goal_content_pred + suffix_pred
        
        init2_pddl_gt = prefix_gt + init_content_gt + middle_gt + init_content_gt + suffix_gt
        goal2_pddl_gt = prefix_gt + goal_content_gt + middle_gt + goal_content_gt + suffix_gt
        
        _, _, init2_correct = evaluate_pddl(domain, init2_pddl_gt, init2_pddl_pred, is_placeholder)
        _, _, goal2_correct = evaluate_pddl(domain, goal2_pddl_gt, goal2_pddl_pred, is_placeholder)
        if not init2_correct:
            feedback.append("The initial state is incorrect.") # The PDDL representation of the initial state (:init ...) is not faithful to the natural language description
        if not goal2_correct:
            feedback.append("The goal state is incorrect.") # The PDDL representation of the goal state (:goal ...) is not faithful to the natural language description
        
    return {
        "parseable": parseable,
        "solvable": solvable,
        "correct": correct,
        "feedback": feedback
    }

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