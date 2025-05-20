import os
import json
from utils.io_utils import load_json_data, save_data_to_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_experience_pool():
    id_trial_pairs = []
    id_trial_pairs_path = os.path.join(BASE_DIR, "exps", f"id_trial_pairs.json")
    save_data_to_json(id_trial_pairs, id_trial_pairs_path)

def insert_new_exp(task, trial, reflection_on_previous_trial, agent_resp, eval):
    exp = {
        "task": task,
        "trial": trial,
        "reflection_on_previous_trial": reflection_on_previous_trial,
        "agent_resp": agent_resp,
        "eval": eval
    }
    
    exp_path = os.path.join(BASE_DIR, "exps", f"task_{task["id"]}_trial_{trial}.json")
    save_data_to_json(exp, exp_path)

    id_trial_pairs_path = os.path.join(BASE_DIR, "exps", f"id_trial_pairs.json")
    id_trial_pairs = load_json_data(id_trial_pairs_path)
    id_trial_pairs.append((task["id"], trial))
    save_data_to_json(id_trial_pairs, id_trial_pairs_path)

def load_experience_pool():
    id_trial_pairs_path = os.path.join(BASE_DIR, "exps", f"id_trial_pairs.json")
    id_trial_pairs = load_json_data(id_trial_pairs_path)

    experiences = []
    for id, trial in id_trial_pairs:
        exp_path = os.path.join(BASE_DIR, "exps", f"task_{id}_trial_{trial}.json")
        exp = load_json_data(exp_path)
        experiences.append(exp)
    
    return experiences

def get_successful_trials():
    experiences = load_experience_pool()
    return [exp for exp in experiences if exp["eval"]["correct"]]