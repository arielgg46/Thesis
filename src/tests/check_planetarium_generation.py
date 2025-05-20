import os

from client.client import llm_query
from dataset.dataset import load_planetarium_subset, select_and_save_planetarium_subset_sql
from domains.utils import get_domain_description, get_domain_pddl
from utils.io_utils import save_data_to_json, load_json_data
from utils.tokens_utils import count_tokens

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "dataset-v2.db")

train_pairs = [
# gripper
('evenly_distributed', 'one_room'),
('holding', 'pickup'),
('one_room', 'n_room_distributed'),
('one_room', 'evenly_distributed'),
('evenly_distributed', 'pickup'),
('one_room', 'focus_max'),
('holding', 'evenly_distributed'),
('holding', 'n_room_distributed'),
('n_room_distributed', 'holding'),
('holding', 'focus_max'),
('evenly_distributed', 'evenly_distributed'),
('evenly_distributed', 'n_room_distributed'),
('n_room_distributed', 'one_room'),
('holding', 'one_room'),
('n_room_distributed', 'pickup'),
('one_room', 'holding'),
('one_room', 'one_room'),
('n_room_distributed', 'evenly_distributed'),
('one_room', 'pickup'),
('holding', 'holding'),
('n_room_distributed', 'n_room_distributed'),
('n_room_distributed', 'focus_max'),
('evenly_distributed', 'holding'),
# blocksworld
('staircase', 'stack'),
('on_table', 'equal_towers'),
('tower', 'on_table'),
('staircase', 'on_table'),
('holding_one', 'equal_towers'),
('tower', 'equal_towers'),
('holding_one', 'stack'),
('stack', 'holding_one'),
('equal_towers', 'holding_one'),
('staircase', 'equal_towers'),
('equal_towers', 'staircase'),
('stack', 'staircase'),
('on_table', 'staircase'),
('stack', 'tower'),
('equal_towers', 'tower'),
('holding_one', 'staircase'),
('tower', 'holding_one'),
('on_table', 'tower'),
('tower', 'staircase'),
('staircase', 'holding_one'),
('staircase', 'staircase'),
('holding_one', 'tower'),
('tower', 'tower'),
('equal_towers', 'stack'),
('staircase', 'tower'),
('stack', 'stack'),
('stack', 'on_table'),
('equal_towers', 'on_table'),
('on_table', 'stack'),
('stack', 'equal_towers'),
('equal_towers', 'equal_towers'),
('tower', 'stack'),
]

test_pairs = [
# floor-tile
('grid', 'all_different'),
('rings', 'paint_x'),
('grid', 'checkerboard'),
('grid', 'paint_all'),
('rings', 'checkerboard'),
('disconnected_rows', 'disconnected_rows'),
('rings', 'rings'),
('rings', 'paint_all'),
('grid', 'paint_x'),
# gripper
('swap', 'swap'),
('holding', 'focus_min'),
('holding', 'drop_and_pickup'),
('one_room', 'drop_and_pickup'),
('one_room', 'focus_min'),
('n_room_distributed', 'focus_min'),
('juggle', 'juggle'),
# blocksworld
('swap', 'swap'),
('invert', 'invert'),
]

def save_subsets():
    select_and_save_planetarium_subset_sql(DATASET_PATH, train_pairs, 1, "train3")
    select_and_save_planetarium_subset_sql(DATASET_PATH, test_pairs, 1, "test3")

# save_subsets()

def save_tasks_by_init_goal_abs():
    train_dataset = load_planetarium_subset("train3")
    test_dataset = load_planetarium_subset("test3")

    train_init = set()
    train_goal = set()
    test_init = set()
    test_goal = set()

    for init, goal in train_pairs:
        train_goal.add(goal)
        train_init.add(init)

    for init, goal in test_pairs:
        test_goal.add(goal)
        test_init.add(init)

    print(train_init)
    print()
    print(train_goal)
    print()
    print(test_init)
    print()
    print(test_goal)

    num_objects_range = [15, 30]
    init_num_propositions_range = [30, 50]
    goal_num_propositions_range = [1, 50]

    def in_between(val, rang):
        if rang[0] <= val and val <= rang[1]:
            return True
        return False

    tasks_by_init = {}

    for init in train_init:
        tasks_by_init[init] = []
        for abstraction in [True]:
        # for abstraction in [False, True]:
            ok = False
            for task in train_dataset:
                task_init = task["init"]
                if task_init != init:
                    continue
                init_is_abstract = task["init_is_abstract"]
                num_objects = task["num_objects"]
                init_num_propositions = task["init_num_propositions"] 
                goal_num_propositions = task["goal_num_propositions"]
                if init_is_abstract == abstraction and in_between(num_objects, num_objects_range) and in_between(init_num_propositions, init_num_propositions_range) and in_between(goal_num_propositions, goal_num_propositions_range):
                    ok = True
                    tasks_by_init[init].append(task)
                    break
            if not ok:
                print(f"Task not found for init: {init} and abstraction: {abstraction}")
                tasks_by_init[init].append(None)

    for init in test_init:
        tasks_by_init[init] = []
        for abstraction in [True]:
        # for abstraction in [False, True]:
            ok = False
            for task in test_dataset:
                task_init = task["init"]
                if task_init != init:
                    continue
                init_is_abstract = task["init_is_abstract"]
                num_objects = task["num_objects"]
                init_num_propositions = task["init_num_propositions"] 
                goal_num_propositions = task["goal_num_propositions"]
                if init_is_abstract == abstraction and in_between(num_objects, num_objects_range) and in_between(init_num_propositions, init_num_propositions_range) and in_between(goal_num_propositions, goal_num_propositions_range):
                    ok = True
                    tasks_by_init[init].append(task)
                    break
            if not ok:
                print(f"Task not found for init: {init} and abstraction: {abstraction}")
                tasks_by_init[init].append(None)


    tasks_by_goal = {}

    for goal in train_goal:
        tasks_by_goal[goal] = []
        for abstraction in [True]:
        # for abstraction in [False, True]:
            ok = False
            for task in train_dataset:
                task_goal = task["goal"]
                if task_goal != goal:
                    continue
                goal_is_abstract = task["goal_is_abstract"]
                num_objects = task["num_objects"]
                init_num_propositions = task["init_num_propositions"] 
                goal_num_propositions = task["goal_num_propositions"]
                if goal_is_abstract == abstraction and in_between(num_objects, num_objects_range) and in_between(init_num_propositions, init_num_propositions_range) and in_between(goal_num_propositions, goal_num_propositions_range):
                    ok = True
                    tasks_by_goal[goal].append(task)
                    break
            if not ok:
                print(f"Task not found for goal: {goal} and abstraction: {abstraction}")
                tasks_by_goal[goal].append(None)

    for goal in test_goal:
        tasks_by_goal[goal] = []
        for abstraction in [True]:
        # for abstraction in [False, True]:
            ok = False
            for task in test_dataset:
                task_goal = task["goal"]
                if task_goal != goal:
                    continue
                goal_is_abstract = task["goal_is_abstract"]
                num_objects = task["num_objects"]
                init_num_propositions = task["init_num_propositions"] 
                goal_num_propositions = task["goal_num_propositions"]
                if goal_is_abstract == abstraction and in_between(num_objects, num_objects_range) and in_between(init_num_propositions, init_num_propositions_range) and in_between(goal_num_propositions, goal_num_propositions_range):
                    ok = True
                    tasks_by_goal[goal].append(task)
                    break
            if not ok:
                print(f"Task not found for goal: {goal} and abstraction: {abstraction}")
                tasks_by_goal[goal].append(None)

    print(len(tasks_by_init))
    print()
    print(len(tasks_by_goal))

    init_tokens = []
    for init in tasks_by_init:
        for task in tasks_by_init[init]:
            if task is None:
                continue
            nl = task["natural_language"]
            pddl = task["problem_pddl"]
            domain = task["domain"]
            domain_pddl = get_domain_pddl(domain)
            domain_description = get_domain_description(domain)
            tokens = [count_tokens(nl), count_tokens(pddl), count_tokens(domain_pddl), count_tokens(domain_description)]
            total = sum(tokens)
            print(tokens, total)
            init_tokens.append(total)

    goal_tokens = []
    for goal in tasks_by_goal:
        for task in tasks_by_goal[goal]:
            if task is None:
                continue
            nl = task["natural_language"]
            pddl = task["problem_pddl"]
            domain = task["domain"]
            domain_pddl = get_domain_pddl(domain)
            domain_description = get_domain_description(domain)
            tokens = [count_tokens(nl), count_tokens(pddl), count_tokens(domain_pddl), count_tokens(domain_description)]
            total = sum(tokens)
            print(tokens, total)
            goal_tokens.append(total)

    print(sum(init_tokens), sum(goal_tokens))

    tasks_by_init_path = os.path.join(BASE_DIR, "tasks_by_init.json")
    tasks_by_goal_path = os.path.join(BASE_DIR, "tasks_by_goal.json")
    save_data_to_json(tasks_by_init, tasks_by_init_path)
    save_data_to_json(tasks_by_goal, tasks_by_goal_path)

# save_tasks_by_init_goal_abs()

def check_generation(task, state):
    nl = task["natural_language"]
    pddl = task["problem_pddl"]
    domain = task["domain"]
    domain_pddl = get_domain_pddl(domain)
    domain_description = get_domain_description(domain)
    
    system_prompt = f"""You are an advanced reasoning agent. You will be given a planning domain, it's description and PDDL, and the natural language description and PDDL of a problem in this domain.

    Your task is to reason in a single short paragraph whether the {state} state of the problem PDDL is equivalent to the corresponding natural language description of this {state} state. After the single reasoning paragraph, write a single EQUIVALENT or NOT EQUIVALENT.
"""
    
    user_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Natural language description of the problem:
{nl}

Problem PDDL:
{pddl}

Your reasoning and answer on the equivalence:
"""

    resp = llm_query(system_prompt, user_prompt)
    return resp

def check_all_generations():
    tasks_by_init_path = os.path.join(BASE_DIR, "tasks_by_init.json")
    tasks_by_goal_path = os.path.join(BASE_DIR, "tasks_by_goal.json")
    tasks_by_init = load_json_data(tasks_by_init_path)
    tasks_by_goal = load_json_data(tasks_by_goal_path)
    
    # for init in tasks_by_init:
    #     print(init)
    #     for task in tasks_by_init[init]:
    #         if task is None:
    #             continue
    #         resp = check_generation(task, "init")
    #         content = resp.choices[0].message.content
    #         if "NOT EQUIVALENT" in content:
    #             print(task)
    #             print(content)
    #             print()
    #         else:
    #             print("OK")

    
    for goal in tasks_by_goal:
        print(goal)
        for task in tasks_by_goal[goal]:
            if task is None:
                continue
            resp = check_generation(task, "goal")
            content = resp.choices[0].message.content
            if "NOT EQUIVALENT" in content:
                print(task)
                print(content)
                print()
            else:
                print("OK")

check_all_generations()
