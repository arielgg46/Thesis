import os
import json
import time
import datetime

from dataset.dataset import load_planetarium_subset
from validator.validator import validate_plan
from visualizer.visualizer import visualize_agent_evaluations
from config import BASE_DIR, VAL_PATH, RESULT_ROOT, EXP_TRAINING_TRIALS, LLM_DEFAULT_MODEL
from exp.training import train
# from exp.insights_extraction import extract_insights, parse_rules, update_rules, save_rules, load_rules
from exp.rag import get_top_similar_successes
from exp.eval_trial import eval_trial
from agents.modeler_agents import get_modeler_agent
from agents.planner_agents import get_planner_agent

from utils.io_utils import save_text, make_case_dir
from utils.evaluation_utils import evaluate_pddl
from utils.planning_utils import generate_plan
from utils.result_utils import initialize_result_structures
from utils.pddl_utils import get_pddl_substr, extract_typed_objects

os.makedirs(RESULT_ROOT, exist_ok=True)

def set_fsp_example(domain, subset, id):
    dataset = load_planetarium_subset(subset)
    ex = [ex for ex in dataset if ex["id"] == id][0:1][0]

    domain_folder_path = os.path.join(BASE_DIR, "domains", domain)
    domain_path = os.path.join(domain_folder_path, "domain.pddl")
    nl_path = os.path.join(domain_folder_path, "fsp_ex_nl.txt")
    pddl_path = os.path.join(domain_folder_path, "fsp_ex_pddl.pddl")
    plan_path = os.path.join(domain_folder_path, "fsp_ex_plan.pddl")
    objects_path = os.path.join(domain_folder_path, "fsp_ex_objects.json")

    nl = ex["natural_language"]
    pddl = ex["problem_pddl"]

    save_text(nl_path, nl)
    save_text(pddl_path, pddl)

    plan = generate_plan(domain_path, pddl_path)
    objects = extract_typed_objects(pddl)

    save_text(plan_path, plan)
    # save_text(objects_path, objects)
    with open(objects_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=4)
                
def run_evaluations():
    print("⚙️ Loading dataset subsets...")
    try:
        train_dataset = load_planetarium_subset("train4")
        test_dataset = load_planetarium_subset("test4")
        print("  ☑️ Loaded dataset subsets")
    except Exception as e:
        print("❌ Failed to load dataset subsets", e)

    agent_results_structure = {}
    domain_results_structure = {}

    print("⚙️ Selecting problems...")
    # selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][1:2]

    # selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][55:57]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][55:57]
    selected_cases = [ex for ex in test_dataset if ex["domain"]=="floor-tile"][15:16]

    print(f"  ☑️ {len(selected_cases)} problems selected")
    
    active_agents = [
        # "llm_planner", 
        # "llm_planner_fsp", 
        # "llm_plus_p", 
        # "llm_plus_p_fsp", 
        # "gcd", 
        # "daps_gcd", 
        # "daps_gcd_r",
        # "daps_gcd_fsp", 
        "daps_gcd_r_fsp" 
    ]

    planning_agents = [
        "llm_planner",
        "llm_planner_fsp"
    ]

    llm_model = "accounts/fireworks/models/deepseek-v3"

    for agent_name in active_agents:
        if agent_name in planning_agents:
            agent = get_planner_agent(agent_name, llm_model)
        else:
            agent = get_modeler_agent(agent_name, llm_model, llm_model, llm_model)
        print(f"\n🔧 Running agent: {agent_name}")
        for ex in selected_cases:
            idx = ex["id"]
            domain = ex["domain"]
            nl = ex["natural_language"]
            pddl_gt = ex["problem_pddl"]
            is_placeholder = ex["is_placeholder"]
            agent.set_task(domain, nl)

            print(f"\n🚀 Starting problem: {domain}_{idx}")

            dom_path = os.path.join(BASE_DIR, "domains", domain, "domain.pddl")
            case_dir = make_case_dir(RESULT_ROOT, agent_name, domain, idx)

            print("⏫ Storing natural language description and PDDL ground truth...")
            save_text(os.path.join(case_dir, "nl.txt"), nl)
            save_text(os.path.join(case_dir, "pddl_gt.pddl"), pddl_gt)
            print("  ☑️ Done")

            print("🤖 Generating prediction...")
            start_time = time.time()
            resp = agent.solve_task()
            generation_time = time.time() - start_time
            print(f"  ☑️ Done in {generation_time:.2f}s")

            prompt_tokens = resp["prompt_tokens"]
            completion_tokens = resp["completion_tokens"]
            total_tokens = resp["total_tokens"]
            print(f"  Used {prompt_tokens} tokens in prompt + {completion_tokens} tokens in completion = {total_tokens} tokens in total.")

            if agent_name in planning_agents:
                plan_pred = resp["plan"]
                pred_path = os.path.join(case_dir, f"plan_pred.pddl")
                save_text(pred_path, plan_pred)

                print("📋 Evaluating generated Plan...")
                is_valid, val_output = validate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"), pred_path, VAL_PATH, case_dir)
                # print("VAL OUTPUT")
                # print(val_output)
                if is_valid:
                    print("  ✅ Valid plan")
                else:
                    print("  ❌ Not valid plan")

                eval_result = {"is_valid" : is_valid, "val_output": val_output, **resp}
            else:
                pddl_pred = resp["problem_pddl"]
                pddl_pred = get_pddl_substr(pddl_pred)
                pred_path = os.path.join(case_dir, f"pddl_pred.pddl")
                save_text(pred_path, pddl_pred)

                print("📋 Evaluating generated PDDL...")
                eval_result = eval_trial(ex, resp)
                parseable = eval_result["parseable"]
                solvable = eval_result["solvable"]
                correct = eval_result["correct"]

                eval_result.update(resp)
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
                print(eval_result["feedback"])

            dom_dict_a, prob_dict = initialize_result_structures(
                agent_results_structure,
                domain_results_structure,
                agent_name,
                domain,
                dom_path,
                ex,
                eval_result,
                resp,
                llm_model
            )

            if agent_name not in planning_agents:
                print("📐 Planning on generated PDDL...")
                if solvable:
                    plan_pred = generate_plan(dom_path, pred_path)
                    plan_gt = generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"))
                    if plan_pred:
                        save_text(os.path.join(case_dir, "plan_pred.txt"), plan_pred)
                        dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                        prob_dict["agents"][agent_name]["plan_pred"] = plan_pred
                    print("  ☑️ Done")
                else:
                    print("  ⏭️ Skipping predicted planning: not solvable")
            else:
                dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                prob_dict["agents"][agent_name]["plan_pred"] = plan_pred

            dom_dict_a["problems"][idx]["generation_time"] = generation_time
            prob_dict["agents"][agent_name]["generation_time"] = generation_time

            # Se puede hacer una sola vez por problema
            print("📐 Planning on ground truth...")
            plan_gt = generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"))
            if plan_gt:
                save_text(os.path.join(case_dir, "plan_gt.txt"), plan_gt)
                dom_dict_a["problems"][idx]["plan_gt"] = plan_gt
                prob_dict["plan_gt"] = plan_gt
            print("  ☑️ Done")

            print(f"🏁 Finished problem: {domain}_{idx}")

    # Guardar resultados
    print("⏫ Storing results...")
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(RESULT_ROOT, f"evaluation_by_agent_{now}.json"), "w", encoding="utf-8") as f:
        json.dump(agent_results_structure, f, indent=4)
    with open(os.path.join(RESULT_ROOT, f"evaluation_by_domain_{now}.json"), "w", encoding="utf-8") as f:
        json.dump(domain_results_structure, f, indent=4)
    print("  ☑️ Done")

    print("\n🎉 Pipeline complete.")

def visualize_evaluation(eval_name):
    visualize_agent_evaluations(eval_name, RESULT_ROOT)

def eval_exp():
    print("⚙️ Loading dataset subsets...")
    try:
        train_dataset = load_planetarium_subset("train2")
        test_dataset = load_planetarium_subset("test2")
        print("  ☑️ Loaded dataset subsets")
    except Exception as e:
        print("❌ Failed to load dataset subsets", e)

    print("⚙️ Selecting problems...")
    # selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][10:11]

    selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][5:7]
    # selected_cases = [ex for ex in train_dataset if ex["domain"]=="gripper"][10:11]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][5:9]

    print("Training")
    train(selected_cases, 3, API_KEY, model="accounts/fireworks/models/deepseek-v3")

# extract_insights(API_KEY, model="accounts/fireworks/models/deepseek-v3")

def prep():
    print("⚙️ Loading dataset subsets...")
    train_dataset = load_planetarium_subset("train2")
    
    print("⚙️ Selecting problems...")
    selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][5:7]
    
    train(selected_cases, EXP_TRAINING_TRIALS, API_KEY, model = LLM_DEFAULT_MODEL)
    
    extract_insights(API_KEY, LLM_DEFAULT_MODEL)

    insights = load_rules()


# set_fsp_example("floor-tile", "test2", 180758)

# from pprint import pprint 

# rules = load_rules()
# pprint(rules)
# print()

# operations = "ADD 1: Ensure the goal state accurately reflects the problem's requirements, particularly in terms of the desired configurations and relationships between objects.\n\nADD 2: Validate that the goal state is achievable from the initial state by ensuring all necessary preconditions are met.\n\nADD 3: Double-check the alignment between the problem's natural language description and the generated PDDL to avoid inconsistencies.\n\nADD 4: Consider the overall structure and constraints of the domain when formulating the goal state to ensure it is both valid and solvable."
# operations = parse_rules(operations)
# pprint(operations)
# print()

# rules = update_rules(rules, operations, False)
# pprint(rules)
# print()

# operations = "EDIT 2: Ensure the goal and init state accurately reflects the problem's requirements, particularly in terms of the desired configurations and relationships between objects."
# operations = parse_rules(operations)
# pprint(operations)
# print()

# rules = update_rules(rules, operations, False)
# pprint(rules)
# print()

# save_rules(rules)

# subset_name = "train2"
    
# subset = load_planetarium_subset(subset_name)

# task = subset[3]
# task_id = task["id"]

# print(task)
# print(task["natural_language"])
# print()
# print(embedding)

# k = 3
# similar_successes = get_top_similar_successes(task_id, subset_name, k)

# pprint(similar_successes)

# eval_exp()

run_evaluations()

# extract_insights(API_KEY, LLM_DEFAULT_MODEL)
# visualize_evaluation("evaluation_by_agent_2025-05-01_18-26-35.json")

# All FSP examples have abstract init and explicit goal, from 10 to 20 objects, init and goal propositions, and planning steps
# set_fsp_example("blocksworld","train2", 19014)
# set_fsp_example("gripper","train2", 102638)
# set_fsp_example("floor-tile","test2", 181746)

# domain = "blocksworld"

# init_gt =   "(arm-empty) (clear b1) (clear b2) (clear b4) (clear b7) (on b2 b3) (on b4 b5) (on b5 b6) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b1) (on-table b10) (on-table b3) (on-table b6)"
# goal_gt =   "(arm-empty) (on b2 b1) (on b3 b2) (on b4 b3) (on b5 b4) (on b6 b5) (on b7 b6) (on b8 b7) (on b9 b8) (on b10 b9) (clear b10) (on-table b1)"

# init_pred = "(arm-empty) (clear b1) (clear b2) (clear b4) (clear b7) (on b1 b3) (on b4 b5) (on b5 b6) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b2) (on-table b10) (on-table b3) (on-table b6)"
# goal_pred = "(arm-empty) (on b2 b10) (on b3 b2) (on b4 b3) (on b5 b4) (on b6 b5) (on b7 b6) (on b8 b7) (on b9 b8) (on b1 b9) (clear b1) (on-table b10)"

# pddl_gt =   f"(define (problem tower_to_stack_1_2_3_4)\n    (:domain blocksworld)\n    (:requirements :strips)\n    (:objects b1 b10 b2 b3 b4 b5 b6 b7 b8 b9)\n    (:init {goal_gt})\n    (:goal (and {goal_gt}))\n)"
# pddl_pred =   f"(define (problem tower_to_stack_1_2_3_4)\n    (:domain blocksworld)\n    (:requirements :strips)\n    (:objects b1 b10 b2 b3 b4 b5 b6 b7 b8 b9)\n    (:init {goal_pred})\n    (:goal (and {goal_pred}))\n)"

# parseable, solvable, correct = evaluate_pddl(domain = domain, pddl_gt = pddl_gt, pddl_pred = pddl_pred, is_placeholder = False)

# if parseable:
#     print("  ✅ Parseable")
# else:
#     print("  ❌ Not parseable")
# if solvable:
#     print("  ✅ Solvable")
# else:
#     print("  ❌ Not solvable")
# if correct:
#     print("  ✅ Correct")
# else:
#     print("  ❌ Not correct")