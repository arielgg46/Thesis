import re
import os, json
import datetime
from typing import List, Tuple, Dict
from collections import defaultdict
from pprint import pprint

from utils.io_utils import save_data_to_json, load_json_data
from exp.experience_pool import load_experience_pool
from agents.insights_agent import compare_fail_vs_succ, compare_successes
from config import INSIGHTS_LIMIT

def extract_insights(resume: bool, model: str):
    if not resume:
        choice = input("Are you sure you want to restart the insights extraction? Any progress will be lost (y/n):")
        if choice == "n" or choice == "N":
            return
        
    # Load Experience Pool
    experience_pool = load_experience_pool()
    # print(f"############ EXPERIENCES ############")
    # pprint(experience_pool)
    # print([(exp["task"]["id"], exp["eval"]["correct"]) for exp in experience_pool])
    # print()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # RESTART OR RESUME
    progress_path = os.path.join(BASE_DIR, "insights_extraction_progress.json")
    if resume:
        progress = load_json_data(progress_path)
    else:
        progress = {
            "mode": "same_task_fail_vs_success",
            "idx": 0
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)
    mode_start = progress["mode"]
    idx_start = progress["idx"]

    insights = load_insights()

    # Build batches of successes
    successes = [exp for exp in experience_pool if exp["eval"]["correct"]] # maybe apply random shuffle
    batch_of_successes_size = 2
    batches_of_successes = []

    dom_to_succs = {}
    for success in successes:
        domain = success["task"]["domain"]
        if not (domain in dom_to_succs):
             dom_to_succs[domain] = []
        dom_to_succs[domain].append(success)

    for domain in dom_to_succs:
        cur_batch = []
        for success in dom_to_succs[domain]:
            cur_batch.append(success)
            if len(cur_batch) == batch_of_successes_size:
                batches_of_successes.append(cur_batch)
                cur_batch = []


    if mode_start == "same_task_fail_vs_success":
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

        # Insights from fail vs success pairs
        print(f"############ INSIGHTS FROM FAIL VS SUCCESS PAIRS ############")
        for i in range(idx_start, len(same_task_fail_success_pairs)):
            fail, succ = same_task_fail_success_pairs[i]
            
            progress = {
                "mode": "same_task_fail_vs_success",
                "idx": i
            }
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=4)

            print(f"############ INSIGHTS AGENT RESPONSE ############")
            domain = succ["task"]["domain"]
            insights_agent_resp = compare_fail_vs_succ(succ, fail, insights, model)
            operations = insights_agent_resp["operations"]
            pprint(operations)
            print()

            print(f"############ PARSED OPERATIONS ############")
            parsed_operations = parse_operations(operations)
            pprint(parsed_operations)
            print()

            print(f"############ RECTIFIED OPERATIONS AND NEW INSIGHTS ############")
            rectified_operations = []
            for insight_type in parsed_operations:
                if insight_type == "DOMAIN_KNOWLEDGE":
                    insights_subset = insights["agent"]["domain"][domain]["world_knowledge"]
                elif insight_type == "DOMAIN_RULES":
                    insights_subset = insights["agent"]["domain"][domain]["rules"]
                elif insight_type == "GENERAL":
                    insights_subset = insights["agent"]["general"]["rules"]
                else:
                    continue

                list_full = (len(insights_subset) >= INSIGHTS_LIMIT)

                rectified_operations_subset, insights_subset = update_insights(insights_subset, parsed_operations[insight_type], list_full)
                rectified_operations += rectified_operations_subset

                if insight_type == "DOMAIN_KNOWLEDGE":
                    insights["agent"]["domain"][domain]["world_knowledge"] = insights_subset
                elif insight_type == "DOMAIN_RULES":
                    insights["agent"]["domain"][domain]["rules"] = insights_subset
                elif insight_type == "GENERAL":
                    insights["agent"]["general"]["rules"] = insights_subset
            pprint(rectified_operations)
            print()
            pprint(insights)
            print()
            save_operations(insights_agent_resp["operations"], parsed_operations, rectified_operations)
            save_insights(insights)
        idx_start = 0

    # Insights from batches of successes
    print(f"############ INSIGHTS FROM BATCHES OF SUCCESSES ############")
    for i in range(idx_start, len(batches_of_successes)):
        successes = batches_of_successes[i]
        progress = {
            "mode": "batches_of_successes",
            "idx": i
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)

        print(f"############ INSIGHTS AGENT RESPONSE ############")
        domain = successes[0]["task"]["domain"]
        insights_agent_resp = compare_successes(successes, insights, model)
        operations = insights_agent_resp["operations"]
        pprint(operations)
        print()

        print(f"############ PARSED OPERATIONS ############")
        parsed_operations = parse_operations(operations)
        pprint(parsed_operations)
        print()

        print(f"############ RECTIFIED OPERATIONS AND NEW INSIGHTS ############")
        rectified_operations = []
        for insight_type in parsed_operations:
            if insight_type == "DOMAIN_KNOWLEDGE":
                insights_subset = insights["agent"]["domain"][domain]["world_knowledge"]
            elif insight_type == "DOMAIN_RULES":
                insights_subset = insights["agent"]["domain"][domain]["rules"]
            elif insight_type == "GENERAL":
                insights_subset = insights["agent"]["general"]["rules"]
            else:
                continue

            list_full = (len(insights_subset) >= INSIGHTS_LIMIT)

            rectified_operations_subset, insights_subset = update_insights(insights_subset, parsed_operations[insight_type], list_full)
            rectified_operations += rectified_operations_subset

            if insight_type == "DOMAIN_KNOWLEDGE":
                insights["agent"]["domain"][domain]["world_knowledge"] = insights_subset
            elif insight_type == "DOMAIN_RULES":
                insights["agent"]["domain"][domain]["rules"] = insights_subset
            elif insight_type == "GENERAL":
                insights["agent"]["general"]["rules"] = insights_subset
        pprint(rectified_operations)
        print()
        pprint(insights)
        print()
        save_operations(insights_agent_resp["operations"], parsed_operations, rectified_operations)
        save_insights(insights)
    
    progress = {
        "done": "yes"
    }
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)


def save_insights(insights: Dict):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    insights_path = os.path.join(BASE_DIR, "insights.json")
    save_data_to_json(insights, insights_path)

def load_insights() -> Dict:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    insights_path = os.path.join(BASE_DIR, "insights.json")
    return load_json_data(insights_path)

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
def _parse_operations(llm_text):
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

def parse_operations(llm_text):
    """
    Parses LLM output formatted as:
    <INSIGHT TYPE> <OPERATION> <INSIGHT NUMBER>: <INSIGHT TEXT>
    
    Returns a dict with keys: 'DOMAIN_KNOWLEDGE', 'DOMAIN_RULES', 'GENERAL'
    Each key maps to a list of tuples: (OPERATION, INSIGHT NUMBER, INSIGHT TEXT)
    """
    # Compile regex pattern
    pattern = r'^(DOMAIN_KNOWLEDGE|DOMAIN_RULES|GENERAL)\s+(AGREE|REMOVE|EDIT|ADD)\s+(\d+):\s+(.*)$'
    lines = llm_text.strip().splitlines()
    
    # Defaultdict of lists for grouping by insight type
    results = defaultdict(list)

    # Loop through each line
    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            insight_type, operation, number, text = match.groups()
            text = text.strip()
            
            # Heuristic: Avoid clearly malformed or cutoff completions
            if text and text.endswith('.') and not any(op in text for op in ['AGREE', 'EDIT', 'REMOVE', 'ADD']):
                results[insight_type].append((operation, int(number), text))

    return dict(results)

def retrieve_insight_index(insights, operation_insight_text):
    for i in range(len(insights)):
        if insights[i][0] in operation_insight_text:
            return i

def is_existing_insight(insights, operation_insight_text):
    for i in range(len(insights)):
        if insights[i][0] in operation_insight_text:
            return True
    return False

# Given list of tuples with (insight text, number of edits) and tuple of (operations, text), returns updated list of insights and operations
def update_insights(insights: List[Tuple[str, int]], operations: List[Tuple[str, str]], list_full: bool = False):
    # remove problematic operations
    delete_indices = []
    # print("############ OPERATIONS ############")
    # print(operations)
    for i in range(len(operations)):
        operation_type, insight_num, operation_insight_text = operations[i]

        if operation_type == 'ADD':
            if is_existing_insight(insights, operation_insight_text): # if new insight_text is an existing insight ('in')
                delete_indices.append(i)
        else:
            if operation_type == 'EDIT':
                if is_existing_insight(insights, operation_insight_text): # if insight is matching ('in') existing insight, change it to AGREE 
                    insight_num = retrieve_insight_index(insights, operation_insight_text)
                    operations[i] = (f'AGREE {insight_num+1}', insights[insight_num][0])
                elif (insight_num is None) or (insight_num > len(insights)):   # if insight doesn't exist, remove
                    delete_indices.append(i)
                    
            elif operation_type == 'REMOVE' or operation_type == 'AGREE':
                if not is_existing_insight(insights, operation_insight_text): # if new operation_insight_text is not an existing insight
                    delete_indices.append(i)

    operations = [operations[i] for i in range(len(operations)) if i not in delete_indices] # remove problematic operations

    # print("############ RECTIFIED OPERATIONS ############")
    # pprint(operations)
    # print()

    for op in ['REMOVE', 'AGREE', 'EDIT', 'ADD']: # Order is important
        for i in range(len(operations)):
            try:
                operation_type, insight_num, operation_insight_text = operations[i]
            except Exception as e:
                print(e)
                continue

            if operation_type != op:
                continue

            if operation_type == 'REMOVE': # remove insight: -1
                insight_index = retrieve_insight_index(insights, operation_insight_text) # if insight_num doesn't match but text does
                remove_strength = 3 if list_full else 1
                insights[insight_index] = (insights[insight_index][0], insights[insight_index][1]-remove_strength) # -1 (-3 if list full) to the counter
            elif operation_type == 'AGREE': # agree with insight: +1
                insight_index = retrieve_insight_index(insights, operation_insight_text) # if insight_num doesn't match but text does
                insights[insight_index] = (insights[insight_index][0], insights[insight_index][1]+1) # +1 to the counter
            elif operation_type == 'EDIT': # edit the insight: +1 // NEED TO BE AFTER REMOVE AND AGREE
                insight_index = insight_num - 1
                insights[insight_index] = (operation_insight_text, insights[insight_index][1]+1) # +1 to the counter
            elif operation_type == 'ADD': # add new insight: +2
                insights.append((operation_insight_text, 2))
    insights = [insights[i] for i in range(len(insights)) if insights[i][1] > 0] # remove insights when counter reach 0
    insights.sort(key=lambda x: x[1], reverse=True)

    return operations, insights
