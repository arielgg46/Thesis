import os, json
from typing import List
from pprint import pprint

from agents.reflection_agent import reflect
from agents.modeler_agents import ModelerAgent
from utils.evaluation_utils import eval_trial
from utils.io_utils import load_json_data
from exp.experience_pool import insert_new_exp, init_experience_pool

from config import REFLECTION_LLM_MODEL

def get_task_short_desc(task):
    init_abs = goal_abs = "expl"
    if task["init_is_abstract"]:
        init_abs = "abs"
    if task["goal_is_abstract"]:
        goal_abs = "abs"

    task_desc = f"{task["domain"]} {task["id"]} {task["init"]}({init_abs}, {task["init_num_propositions"]}) -> {task["goal"]}({goal_abs}, {task["goal_num_propositions"]}) {task["num_objects"]}"
    return task_desc

def fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning):
    return{
        "nl": fsp_ex_nl,
        "pddl": fsp_ex_pddl,
        "plan": fsp_ex_plan,
        "objects": fsp_ex_objects,
        "reasoning": fsp_ex_reasoning
    }

def store_exp(exps, task, trial, reflection_on_previous_trial, experiential_agent_resp, evaluation):
    exps.append((task, trial, reflection_on_previous_trial, experiential_agent_resp, evaluation))
    return exps

def insert_exps(exps):
    for i in range(len(exps)):
        task, trial, reflection_on_previous_trial, experiential_agent_resp, evaluation = exps[i]
        insert_new_exp(task, trial + 1, reflection_on_previous_trial, experiential_agent_resp, evaluation)

def gather_experiences(resume: bool, agent: ModelerAgent, training_tasks: List[dict], max_trials: int, human_feedback: bool = False):
    if not resume:
        choice = input("Are you sure you want to restart the training? Any progress will be lost (y/n):")
        if choice == "n" or choice == "N":
            return
    
    # init_experience_pool()
    assert len(training_tasks) > 0
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # RESTART OR RESUME
    progress_path = os.path.join(BASE_DIR, "training_progress.json")
    if resume:
        progress = load_json_data(progress_path)
    else:
        progress = {
            "task_id": training_tasks[0]["id"],
            "training_tasks_idx": 0
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)
    training_tasks_idx_start = progress["training_tasks_idx"]

    exps = []
    for i in range(training_tasks_idx_start, len(training_tasks)):
        task = training_tasks[i]
        id = task["id"]

        if len(exps) > 0:
            insert_exps(exps)
        exps = []
        progress = {
            "task_id": id,
            "training_tasks_idx": i
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)

        domain = task["domain"]
        nl = task["natural_language"]
        reflections = []
        agent.set_task(id, domain, nl)

        print(f"## TASK {i + 1} ({id}) ##")
        print(get_task_short_desc(task))
        # pprint(nl)
        # print()

        last_resp = {}

        agent.last_resp = last_resp
        agent.reflections = reflections
        for trial in range(max_trials):
            print(f"## TRIAL {trial + 1} ##")
            # print()

            # print("################## EXPERIENTIAL AGENT RESP ##################")
            experiential_agent_resp = agent.solve_task()
            # pprint(experiential_agent_resp)
            # print()

            print("## EVALUATION ##")
            evaluation = eval_trial(task, experiential_agent_resp)
            parseable = evaluation["parseable"]
            solvable = evaluation["solvable"]
            correct = evaluation["correct"]

            if parseable:
                print("  ✅ Parseable")
            else:
                print("  ❌ Not parseable")
            if solvable:
                print("  ✅ Solvable")
            else:
                print("  ❌ Not solvable")
            if correct:
                print("  ✅ Correct")
            else:
                print("  ❌ Not correct")

            # pprint(evaluation)
            print(evaluation["feedback"])
            print()

            reflection_on_previous_trial = ""
            if trial > 0:
                reflection_on_previous_trial = reflections[-1]
            exps = store_exp(exps, task, trial, reflection_on_previous_trial, experiential_agent_resp, evaluation)

            if evaluation["correct"]:
                break
            else:
                if trial == max_trials - 1:
                    break
                last_resp = experiential_agent_resp
                last_resp["eval"] = evaluation
                agent.last_resp = last_resp
                if trial == max_trials - 2 and human_feedback: # only one trial remaining
                    print("TOO MANY FAILED ATTEMPTS. HUMAN FEEDBACK:")
                    print(task)
                    print(last_resp)
                    print(evaluation)
                    print("HUMAN FEEDBACK")
                    reflection = input()
                else:
                    print("## REFLECTION ##")
                    reflection_agent_resp = reflect(problem_nl = nl, domain = domain, past_reflections = reflections, experiential_agent_resp = experiential_agent_resp, evaluation = evaluation, model = REFLECTION_LLM_MODEL) # To do: improve
                    reflection = reflection_agent_resp["reflection"]
                    # pprint(reflection)
                    # print()
                reflections.append(reflection)
                agent.reflections = reflections
    
    if len(exps) > 0:
        insert_exps(exps)
    progress = {
        "done": "yes"
    }
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)