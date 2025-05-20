import re
import os
import datetime
from typing import List, Tuple
from pprint import pprint

from utils.io_utils import save_data_to_json, load_json_data
from exp.experience_pool import load_experience_pool
from exp.insights_agent import compare_fail_vs_succ, compare_successes

def extract_insights(api_key, model):
    # Load Experience Pool
    experience_pool = load_experience_pool()
    # print(f"############ EXPERIENCES ############")
    # pprint(experience_pool)
    # print()

    # Build batches of successes
    successes = [exp for exp in experience_pool if exp["eval"]["correct"]] # maybe apply random shuffle
    batch_of_successes_size = 2
    batches_of_successes = []
    cur_batch = []
    for success in successes:
        cur_batch.append(success)
        if len(cur_batch) == batch_of_successes_size:
            batches_of_successes.append(cur_batch)
            cur_batch = []

    # Build pairs of (fail, success) for same task
    tasks_by_ids = {}
    for trial in experience_pool:
        id = trial["task"]["id"]
        is_success = trial["eval"]["correct"]
        if id not in tasks_by_ids:
            tasks_by_ids[id] = {"fails": [], "successes": []}
        if is_success:
            tasks_by_ids[id]["successes"].append(trial)
        else:
            tasks_by_ids[id]["fails"].append(trial)
    # maybe apply random shuffle
    same_task_fail_success_pairs = []
    for id in tasks_by_ids:
        for successful_trial in tasks_by_ids[id]["successes"]:
            for failed_trial in tasks_by_ids[id]["fails"]:
                same_task_fail_success_pairs.append((failed_trial, successful_trial))

    rules = load_rules()

    # Insights from fail vs success pairs
    # print(f"############ INSIGHTS FROM FAIL VS SUCCESS PAIRS ############")
    for fail, succ in same_task_fail_success_pairs:
        # print(f"############ INSIGHTS AGENT RESPONSE ############")
        insights_agent_resp = compare_fail_vs_succ(succ, fail, rules, api_key, model)
        operations = insights_agent_resp["operations"]
        # pprint(operations)
        # print()

        # print(f"############ PARSED OPERATIONS ############")
        parsed_operations = parse_operations(operations)
        # pprint(parsed_operations)
        # print()

        # print(f"############ RECTIFIED OPERATIONS AND NEW RULES ############")
        rectified_operations, rules = update_rules(rules, operations, False)
        # pprint(rectified_operations)
        # print()
        # pprint(rules)
        # print()
        save_operations(insights_agent_resp["operations"], parsed_operations, rectified_operations)
        save_rules(rules)


    # Insights from batches of successes
    # print(f"############ INSIGHTS FROM BATCHES OF SUCCESSES ############")
    for successes in batches_of_successes:
        # print(f"############ INSIGHTS AGENT RESPONSE ############")
        insights_agent_resp = compare_successes(successes, rules, api_key, model)
        operations = insights_agent_resp["operations"]
        # pprint(operations)
        # print()

        # print(f"############ PARSED OPERATIONS ############")
        parsed_operations = parse_operations(operations)
        # pprint(parsed_operations)
        # print()

        # print(f"############ RECTIFIED OPERATIONS AND NEW RULES ############")
        rectified_operations, rules = update_rules(rules, parsed_operations, False)
        # pprint(rectified_operations)
        # print()
        # pprint(rules)
        # print()
        save_operations(insights_agent_resp["operations"], parsed_operations, rectified_operations)
        save_rules(rules)


def save_rules(rules):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(BASE_DIR, "rules.json")
    save_data_to_json(rules, rules_path)

def load_rules():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(BASE_DIR, "rules.json")
    return load_json_data(rules_path)

def save_operations(insights_agent_resp, parsed_operations, rectified_operations):
    data = {
        "insights_agent_resp": insights_agent_resp,
        "parsed_operations": parsed_operations,
        "rectified_operations": rectified_operations
    }
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    data_path = os.path.join(BASE_DIR, "operations", f"operations_{now}.json")
    save_data_to_json(data, data_path)
    
############### From ExpeL ###############

# Utils function
def parse_operations(llm_text):
    pattern = r'((?:REMOVE|EDIT|ADD|AGREE)(?: \d+|)): (?:[a-zA-Z\s\d]+: |)(.*)'
    matches = re.findall(pattern, llm_text)

    res = []
    banned_words = ['ADD', 'AGREE', 'EDIT']
    for operation, text in matches:
        text = text.strip()
        if text != '' and not any([w in text for w in banned_words]) and text.endswith('.'):
        # if text is not empty
        # if text doesn't contain banned words (avoid weird formatting cases from llm)
        # if text ends with a period (avoid cut off sentences from llm)
            if 'ADD' in operation:
                res.append(('ADD', text))
            else:
                res.append((operation.strip(), text))
    return(res)

def retrieve_rule_index(rules, operation):
    operation_rule_text = operation[1]
    for i in range(len(rules)):
        if rules[i][0] in operation_rule_text:
            return i

def is_existing_rule(rules, operation_rule_text):
    for i in range(len(rules)):
        if rules[i][0] in operation_rule_text:
            return True
    return False

# Given list of tuples with (rule text, number of edits) and tuple of (operations, text), returns updated list of tuples
def update_rules(rules: List[Tuple[str, int]], operations: List[Tuple[str, str]], list_full: bool = False) -> List[Tuple[str, int]]:
    # remove problematic operations
    delete_indices = []
    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAaa")
    print(operations)
    for i in range(len(operations)):
        operation, operation_rule_text = operations[i]
        operation_type = operation.split(' ')[0]
        rule_num = int(operation.split(' ')[1]) if ' ' in operation else None

        if operation_type == 'ADD':
            if is_existing_rule(rules, operation_rule_text): # if new rule_text is an existing rule ('in')
                delete_indices.append(i)
        else:
            if operation_type == 'EDIT':
                if is_existing_rule(rules, operation_rule_text): # if rule is matching ('in') existing rule, change it to AGREE 
                    rule_num = retrieve_rule_index(rules, (operation, operation_rule_text))
                    operations[i] = (f'AGREE {rule_num+1}', rules[rule_num][0])
                elif (rule_num is None) or (rule_num > len(rules)):   # if rule doesn't exist, remove
                    delete_indices.append(i)
                    
            elif operation_type == 'REMOVE' or operation_type == 'AGREE':
                if not is_existing_rule(rules, operation_rule_text): # if new operation_rule_text is not an existing rule
                    delete_indices.append(i)

    operations = [operations[i] for i in range(len(operations)) if i not in delete_indices] # remove problematic operations

    # print("############ RECTIFIED OPERATIONS ############")
    # pprint(operations)
    # print()

    for op in ['REMOVE', 'AGREE', 'EDIT', 'ADD']: # Order is important
        for i in range(len(operations)):
            operation, operation_rule_text = operations[i]
            operation_type = operation.split(' ')[0]
            if operation_type != op:
                continue

            if operation_type == 'REMOVE': # remove rule: -1
                rule_index = retrieve_rule_index(rules, (operation, operation_rule_text)) # if rule_num doesn't match but text does
                remove_strength = 3 if list_full else 1
                rules[rule_index] = (rules[rule_index][0], rules[rule_index][1]-remove_strength) # -1 (-3 if list full) to the counter
            elif operation_type == 'AGREE': # agree with rule: +1
                rule_index = retrieve_rule_index(rules, (operation, operation_rule_text)) # if rule_num doesn't match but text does
                rules[rule_index] = (rules[rule_index][0], rules[rule_index][1]+1) # +1 to the counter
            elif operation_type == 'EDIT': # edit the rule: +1 // NEED TO BE AFTER REMOVE AND AGREE
                rule_index = int(operation.split(' ')[1])-1
                rules[rule_index] = (operation_rule_text, rules[rule_index][1]+1) # +1 to the counter
            elif operation_type == 'ADD': # add new rule: +2
                rules.append((operation_rule_text, 2))
    rules = [rules[i] for i in range(len(rules)) if rules[i][1] > 0] # remove rules when counter reach 0
    rules.sort(key=lambda x: x[1], reverse=True)

    return operations, rules
