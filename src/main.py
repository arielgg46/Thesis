import os
import json
import time
import datetime

from dataset.dataset import load_planetarium_subset
from agents.dispatcher import generate_with_agent
from validator.validator import validate_plan
from visualizer.visualizer import visualize_agent_evaluations
from config import BASE_DIR, FAST_DOWNWARD_PATH, VAL_PATH, RESULT_ROOT, API_KEY

from utils.io_utils import save_text, make_case_dir
from utils.evaluation_utils import run_evaluation
from utils.planning_utils import try_generate_plan
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

    plan = try_generate_plan(domain_path, pddl_path, FAST_DOWNWARD_PATH, domain_folder_path)
    objects = extract_typed_objects(pddl)

    save_text(plan_path, plan)
    # save_text(objects_path, objects)
    with open(objects_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=4)
                
def run_evaluations():
    print("⚙️ Loading dataset subsets...")
    try:
        train_dataset = load_planetarium_subset("train2")
        test_dataset = load_planetarium_subset("test2")
        print("  ☑️ Loaded dataset subsets")
    except Exception as e:
        print("❌ Failed to load dataset subsets", e)

    agent_results_structure = {}
    domain_results_structure = {}

    print("⚙️ Selecting problems...")
    # selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][1:2]

    selected_cases = [ex for ex in train_dataset if ex["domain"]=="blocksworld"][0:4]
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][0:4]
    selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][0:4]

    print(f"  ☑️ {len(selected_cases)} problems selected")
    
    active_agents = [
        "llm_planner", 
        "llm_planner_fsp", 
        "llm_plus_p", 
        "llm_plus_p_fsp", 
        # "gcd", 
        "daps_gcd", 
        "daps_gcd_r",
        "daps_gcd_fsp" 
    ]

    planning_agents = [
        "llm_planner",
        "llm_planner_fsp"
    ]

    llm_model = "accounts/fireworks/models/deepseek-v3"

    for agent in active_agents:
        print(f"\n🔧 Running agent: {agent}")
        for ex in selected_cases:
            idx = ex["id"]
            domain = ex["domain"]
            nl = ex["natural_language"]
            pddl_gt = ex["problem_pddl"]

            print(f"\n🚀 Starting problem: {domain}_{idx}")

            dom_path = os.path.join(BASE_DIR, "domains", domain, "domain.pddl")
            case_dir = make_case_dir(RESULT_ROOT, agent, domain, idx)

            print("⏫ Storing natural language description and PDDL ground truth...")
            save_text(os.path.join(case_dir, "nl.txt"), nl)
            save_text(os.path.join(case_dir, "pddl_gt.pddl"), pddl_gt)
            print("  ☑️ Done")

            print("🤖 Generating prediction...")
            start_time = time.time()
            resp = generate_with_agent(nl, domain, API_KEY, agent=agent, model=llm_model)
            generation_time = time.time() - start_time
            print(f"  ☑️ Done in {generation_time:.2f}s")

            prompt_tokens = resp["prompt_tokens"]
            completion_tokens = resp["completion_tokens"]
            total_tokens = resp["total_tokens"]
            print(f"  Used {prompt_tokens} tokens in prompt + {completion_tokens} tokens in completion = {total_tokens} tokens in total.")

            if agent in planning_agents:
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
                parseable, solvable, correct = False, False, False
                pddl_pred = resp["problem_pddl"]
                pddl_pred = get_pddl_substr(pddl_pred)
                pred_path = os.path.join(case_dir, f"pddl_pred.pddl")
                save_text(pred_path, pddl_pred)

                print("📋 Evaluating generated PDDL...")
                if domain in ["blocksworld", "gripper"]: # The ones with custom planners
                  print("  📐 Running custom planner...")
                  parseable, solvable, correct = run_evaluation(pddl_gt, pddl_pred)
                else:
                  print("  📐 Running Fast Forward...")
                  parseable, solvable, correct = run_evaluation(pddl_pred, pddl_pred, False)
                  plan = try_generate_plan(dom_path, pred_path, FAST_DOWNWARD_PATH, case_dir)
                  if plan is None:
                      solvable = False
                  else:
                      solvable = True
                
                eval_result = {"parseable": parseable, "solvable": solvable, "correct": correct, **resp}
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

            dom_dict_a, prob_dict = initialize_result_structures(
                agent_results_structure,
                domain_results_structure,
                agent,
                domain,
                dom_path,
                ex,
                eval_result,
                resp,
                llm_model
            )

            if agent not in planning_agents:
                print("📐 Planning on generated PDDL...")
                if solvable:
                    plan_pred = try_generate_plan(dom_path, pred_path, FAST_DOWNWARD_PATH, case_dir)
                    plan_gt = try_generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"), FAST_DOWNWARD_PATH, case_dir)
                    if plan_pred:
                        save_text(os.path.join(case_dir, "plan_pred.txt"), plan_pred)
                        dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                        prob_dict["agents"][agent]["plan_pred"] = plan_pred
                    print("  ☑️ Done")
                else:
                    print("  ⏭️ Skipping predicted planning: not solvable")
            else:
                dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                prob_dict["agents"][agent]["plan_pred"] = plan_pred

            dom_dict_a["problems"][idx]["generation_time"] = generation_time
            prob_dict["agents"][agent]["generation_time"] = generation_time

            # Se puede hacer una sola vez por problema
            print("📐 Planning on ground truth...")
            plan_gt = try_generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"), FAST_DOWNWARD_PATH, case_dir)
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
    
run_evaluations()

# visualize_evaluation("evaluation_by_agent_2025-04-26_00-48-17.json")

# All FSP examples have abstract init and explicit goal, from 10 to 20 objects, init and goal propositions, and planning steps
# set_fsp_example("blocksworld","train2", 19014)
# set_fsp_example("gripper","train2", 102638)
# set_fsp_example("floor-tile","test2", 181746)