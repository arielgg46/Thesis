from typing import List
from pprint import pprint

from exp.modeling_agent import solve_task
from exp.reflection_agent import reflect
from exp.eval_trial import eval_trial
from exp.experience_pool import insert_new_exp, init_experience_pool

from domains.utils import get_fsp_example

def fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning):
    return{
        "nl": fsp_ex_nl,
        "pddl": fsp_ex_pddl,
        "plan": fsp_ex_plan,
        "objects": fsp_ex_objects,
        "reasoning": fsp_ex_reasoning
    }

def train(training_tasks: List[dict], max_trials: int, api_key: str, model: str, human_feedback: bool = False):
    init_experience_pool()
    for task in training_tasks:
        domain = task["domain"]
        nl = task["natural_language"]
        reflections = []

        print("################## TASK ##################")
        pprint(nl)
        print()

        fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning = get_fsp_example(domain)
        init_fsp_examples = [fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning)]
        
        last_resp = {}
        for trial in range(max_trials):
            print(f"################## TRIAL {trial+1} ##################")
            print()

            # modeling_agent_resp = {'objects': ['ball1', 'ball2', 'ball3', 'ball4', 'ball5', 'ball6', 'ball7', 'ball8', 'ball9', 'gripper1', 'gripper2', 'room1', 'room2', 'room3'], 
            # 'problem_pddl': '(define (problem gripper_problem)\n    (:domain gripper)\n    (:requirements :strips)\n    (:objects ball1 ball2 ball3 ball4 ball5 ball6 ball7 ball8 ball9 gripper1 gripper2 room1 room2 room3)\n    (:init \n       (at ball1 room1) (at ball2 room2) (at ball3 room2) (at ball4 room2) (at ball5 room2) (at ball6 room3) (at ball7 room3) (at ball8 room3) (at ball9 room3)        (at-robby room1)\n        (ball ball1) (ball ball2) (ball ball3) (ball ball4) (ball ball5)\n        (ball ball6) (ball ball7) (ball ball8) (ball ball9)\n        (free gripper1) (free gripper2)\n        (gripper gripper1) (gripper gripper2)\n        (room room1) (room room2) (room room3)\n    )\n    (:goal \n        (and \n            (at ball1 room2) (at ball4 room1) (at ball7 room1) (at ball2 room1) (at ball5 room2) (at ball6 room3) (at ball3 room3) (at ball8 room3) (at ball9 room3)))\n)', 'prompt_tokens': [664, 999], 'completion_tokens': [67, 309], 'total_tokens': [731, 1308, 2039]}
            print("################## MODELING AGENT RESP ##################")
            modeling_agent_resp = solve_task(problem_nl = nl, domain = domain, last_resp = last_resp, reflections = reflections, fsp_examples = init_fsp_examples, api_key = api_key, model = model)
            pprint(modeling_agent_resp)
            print()

            print("################## EVALUATION ##################")
            evaluation = eval_trial(task, modeling_agent_resp)
            pprint(evaluation)
            print()

            reflection_on_previous_trial = ""
            if trial > 0:
                reflection_on_previous_trial = reflections[-1]
            insert_new_exp(task, trial + 1, reflection_on_previous_trial, modeling_agent_resp, evaluation)

            if evaluation["correct"]:
                break
            else:
                if trial == max_trials - 1:
                    break
                last_resp = modeling_agent_resp
                if trial == max_trials - 2 and human_feedback: # only one trial remaining
                    print("TOO MANY FAILED ATEMPTS. HUMAN FEEDBACK:")
                    reflection = input()
                else:
                    print("################## REFLECTION ##################")
                    reflecting_agent_resp = reflect(problem_nl = nl, domain = domain, past_reflections = reflections, modeling_agent_resp = modeling_agent_resp, evaluation = evaluation, api_key = api_key, model = model) # To do: improve
                    # pprint(reflecting_agent_resp)
                    reflection = reflecting_agent_resp["reflection"]
                    pprint(reflection)
                    print()
                reflections.append(reflection)