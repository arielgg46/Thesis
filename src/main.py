import os, json, time, datetime, random
from pprint import pprint

from dataset.dataset import load_planetarium_subset
from validator.validator import validate_plan
from visualizer.visualizer import visualize_agent_evaluations
from agents.modeler_agents import get_modeler_agent
from agents.planner_agents import get_planner_agent
from agents.orig_llm_plus_p_agents import get_orig_llm_plus_p_agent
from agents.reflection_agent import reflect
from exp.training import train
from exp.insights_extraction import extract_insights

from utils.io_utils import save_text, make_case_dir, create_file_if_not_exists, load_json_data, save_data_to_json
from utils.evaluation_utils import eval_trial
from utils.planning_utils import generate_plan
from utils.result_utils import initialize_result_structures
from utils.pddl_utils import get_pddl_substr, extract_typed_objects

from config import BASE_DIR, RESULT_ROOT, LLM_DEFAULT_MODEL, TRAINING_SUBSET, TESTING_SUBSET, EXP_TESTING_TRIALS, REFLECTION_LLM_MODEL

os.makedirs(RESULT_ROOT, exist_ok=True)

experiential_agent = get_modeler_agent("exp", LLM_DEFAULT_MODEL, LLM_DEFAULT_MODEL, LLM_DEFAULT_MODEL)

def get_task_short_desc(task):
    init_abs = goal_abs = "expl"
    if task["init_is_abstract"]:
        init_abs = "abs"
    if task["goal_is_abstract"]:
        goal_abs = "abs"

    task_desc = f"{task["domain"]} {task["id"]} {task["init"]}({init_abs}, {task["init_num_propositions"]}) -> {task["goal"]}({goal_abs}, {task["goal_num_propositions"]}) {task["num_objects"]}"
    return task_desc

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
                
def run_evaluations(resume: bool):
    # if not resume:
    #     choice = input("Are you sure you want to restart the evaluation? Any progress will be lost (y/n):")
    #     if choice == "n" or choice == "N":
    #         return
    
    print("⚙️ Loading dataset subsets...")
    try:
        train_dataset = load_planetarium_subset(TRAINING_SUBSET)
        test_dataset = load_planetarium_subset(TESTING_SUBSET)
        print("  ☑️ Loaded dataset subsets")
    except Exception as e:
        print("❌ Failed to load dataset subsets", e)

    agent_results_structure = {}
    domain_results_structure = {}

    print("⚙️ Selecting problems...")
    selected_cases = []
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][1:2]

    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][15:16]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][15:16]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][15:16]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][0:1]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][1:2]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][2:3]
    # selected_cases += [ex for ex in test_dataset][:]
    # selected_cases += [ex for ex in train_dataset][:]

    blocksworld_tasks = [ex for ex in test_dataset if ex["domain"]=="blocksworld"][:]
    gripper_tasks = [ex for ex in test_dataset if ex["domain"]=="gripper"][:]
    floor_tile_tasks = [ex for ex in test_dataset if ex["domain"]=="floor-tile"][:]

    random.seed(42)
    # selected_cases = random.sample(selected_cases, 50)
    selected_cases = random.sample(blocksworld_tasks, 10)+random.sample(gripper_tasks, 10)+random.sample(floor_tile_tasks, 10)

    # selected_cases = [ex for ex in test_dataset if ex["id"] in [109865]]
    
    # [ex for ex in test_dataset if ex["id"] in [109865, 141761, 142306, 164985, 165021, 165028, 165218, 165985, 166118, 166172, 20097, 20197, 92243]]

    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][0:2]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][0:2]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][0:2]


    cases = selected_cases
    seen_ids = []
    selected_cases = []
    for case in cases:
        if not case["id"] in seen_ids:
            selected_cases.append(case)
            seen_ids.append(case["id"])

    for task in selected_cases:
        print(get_task_short_desc(task))

    print(f"  ☑️  {len(selected_cases)} problems selected")
    
    active_agents = [
        # "llm_planner", 
        # "llm_planner_fsp", 
        # "orig_llm_plus_p", 
        # "orig_llm_plus_p_fsp", 
        # "llm_plus_p", 
        # "llm_plus_p_fsp", 
        # "gcd", 
        # "daps_gcd", 
        # "daps_gcd_r",
        # "daps_gcd_fsp",
        # "daps_gcd_r_fsp",
        # "daps_gcd_r_fsp_i",
        # "r_fsp_i"
    ]

    active_agents = [
        "orig_llm_plus_p",
        "llm_plus_p",
        "r",
        "r_o",
        "r_o_gcd",
        "r_o_daps_gcd",

        "orig_llm_plus_p_fsp",
        "llm_plus_p_fsp",
        "r_fsp",
        "r_o_fsp",
        "r_o_gcd_fsp",
        "r_o_daps_gcd_fsp",

        "r_fsp_hi",
        "r_o_daps_gcd_fsp_hi"
    ]

    assert len(active_agents) > 0
    assert len(selected_cases) > 0

    planning_agents = [
        "llm_planner",
        "llm_planner_fsp"
    ]

    original_llm_plus_p_agents = [
        "orig_llm_plus_p", 
        "orig_llm_plus_p_fsp"
    ]

    llm_model = LLM_DEFAULT_MODEL

    # RESTART OR RESUME
    progress_path = os.path.join(BASE_DIR, "evaluations_progress.json")
    if resume:
        progress = load_json_data(progress_path)
        print(f"Resuming evaluation from agent {progress['agent_idx']} ({progress['agent_name']}, task {progress['ex_idx']} ({progress['task_id']}))")
    else:
        progress = {
            "agent_name": active_agents[0],
            "task_id": selected_cases[0]["id"],
            "agent_idx": 0,
            "ex_idx": 0
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)
    agent_idx_start = progress["agent_idx"]
    ex_idx_start = progress["ex_idx"]

    for i in range(agent_idx_start, len(active_agents)):
        agent_name = active_agents[i]
        if agent_name in planning_agents:
            agent = get_planner_agent(agent_name, llm_model)
        else:
            if agent_name in original_llm_plus_p_agents:
                agent = get_orig_llm_plus_p_agent(agent_name, llm_model)
            else:
                agent = get_modeler_agent(agent_name, llm_model, llm_model, llm_model)
        
        trial_dict_path = os.path.join(RESULT_ROOT, agent_name, "trials")
        os.makedirs(trial_dict_path, exist_ok=True)

        plan_pred = ""

        print(f"\n🔧 Running agent: {agent_name}")
        for j in range(ex_idx_start, len(selected_cases)):
            ex_idx_start = 0
            ex = selected_cases[j]
            idx = ex["id"]
            
            progress = {
                "agent_name": agent_name,
                "task_id": idx,
                "agent_idx": i,
                "ex_idx": j
            }
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=4)

            domain = ex["domain"]
            nl = ex["natural_language"]
            pddl_gt = ex["problem_pddl"]
            agent.set_task(idx, domain, nl)

            print(f"\n🚀 Starting problem: {domain}_{idx}")
            print(get_task_short_desc(ex))
            print()

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
            print(f"  Used {prompt_tokens} tokens in prompt + {completion_tokens} tokens in completion = {total_tokens} = {sum(total_tokens)} tokens in total.")

            if agent_name in planning_agents:
                plan_pred = resp["plan"]
                pred_path = os.path.join(case_dir, f"plan_pred.pddl")
                save_text(pred_path, plan_pred)

                print("📋 Evaluating generated Plan...")
                is_valid, val_output = validate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"), pred_path, work_dir = case_dir)
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
                pass
                # print("📐 Planning on generated PDDL...")
                # if solvable:
                #     plan_pred = generate_plan(dom_path, pred_path)
                #     plan_gt = generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"))
                #     if plan_pred:
                #         save_text(os.path.join(case_dir, "plan_pred.txt"), plan_pred)
                #         dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                #         prob_dict["agents"][agent_name]["plan_pred"] = plan_pred
                #     print("  ☑️ Done")
                # else:
                #     print("  ⏭️ Skipping predicted planning: not solvable")
            else:
                dom_dict_a["problems"][idx]["plan_pred"] = plan_pred
                prob_dict["agents"][agent_name]["plan_pred"] = plan_pred

            dom_dict_a["problems"][idx]["generation_time"] = generation_time
            prob_dict["agents"][agent_name]["generation_time"] = generation_time

            # Se puede hacer una sola vez por problema
            # print("📐 Planning on ground truth...")
            # plan_gt = generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"))
            # if plan_gt:
            #     save_text(os.path.join(case_dir, "plan_gt.txt"), plan_gt)
            #     dom_dict_a["problems"][idx]["plan_gt"] = plan_gt
            #     prob_dict["plan_gt"] = plan_gt
            # print("  ☑️ Done")

            trial_dict = {
                "task": ex,
                # "plan_gt": plan_gt,
                # "plan_pred": plan_pred,
                "eval": eval_result,
                "generation_time": generation_time
            }
            with open(os.path.join(trial_dict_path, f"{idx}.json"), "w", encoding="utf-8") as f:
                json.dump(trial_dict, f, indent=4)
            
            print(f"🏁 Finished problem: {domain}_{idx}")

    # Guardar resultados
    print("⏫ Storing results...")
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(RESULT_ROOT, f"evaluation_by_agent_{now}.json"), "w", encoding="utf-8") as f:
        json.dump(agent_results_structure, f, indent=4)
    with open(os.path.join(RESULT_ROOT, f"evaluation_by_domain_{now}.json"), "w", encoding="utf-8") as f:
        json.dump(domain_results_structure, f, indent=4)
    print("  ☑️ Done")

    progress = {
        "done": "yes"
    }
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)
        
    print("\n🎉 Agents evaluation complete.")

def visualize_evaluation(eval_name):
    visualize_agent_evaluations(eval_name, RESULT_ROOT)


def exp_training(resume: bool):
    global experiential_agent
    print("⚙️ Loading dataset subsets...")
    train_dataset = load_planetarium_subset(TRAINING_SUBSET)
    test_dataset = load_planetarium_subset(TESTING_SUBSET)
    
    print("⚙️ Selecting problems...")
    selected_cases = []
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][0:4]
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][0:4]
    selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][0:4]

    selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][16:18]
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][16:18]
    selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][15:17]

    selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][28:30]
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][28:30]
    selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][28:30]

    selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][108:110]
    selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][108:110]
    selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][108:110]
    print(f"{len(selected_cases)} problems selected.")

    print("Training the Experiential Agent...")
    train(resume = resume, agent = experiential_agent, training_tasks = selected_cases, max_trials = 3, human_feedback = True)
    
def insights_extraction(resume: bool):
    print("Extracting insights from experience...")
    extract_insights(resume = resume, model = LLM_DEFAULT_MODEL)

def exp_solve_task(task, human_feedback: bool, max_trials = EXP_TESTING_TRIALS):
    global experiential_agent

    domain = task["domain"]
    nl = task["natural_language"]
    reflections = []
    experiential_agent.set_task(id, domain, nl)

    last_resp = {}
    
    experiential_agent.reflections = reflections
    experiential_agent.last_resp = last_resp
    
    for trial in range(max_trials):
        # print(f"################## TRIAL {trial+1} ##################")
        # print()

        # print("################## MODELING AGENT RESP ##################")
        experiential_agent_resp = experiential_agent.solve_task()
        # pprint(experiential_agent_resp)
        # print()

        # print("################## EVALUATION ##################")
        evaluation = eval_trial(task, experiential_agent_resp)
        # pprint(evaluation)
        # print()

        reflection_on_previous_trial = ""
        if trial > 0:
            reflection_on_previous_trial = reflections[-1]

        if evaluation["correct"]:
            break
        else:
            if trial == max_trials - 1:
                break
            last_resp = experiential_agent_resp
            experiential_agent.last_resp = last_resp
            if trial == max_trials - 2 and human_feedback: # only one trial remaining
                print("TOO MANY FAILED ATTEMPTS. HUMAN FEEDBACK:")
                reflection = input()
            else:
                # print("################## REFLECTION ##################")
                reflection_agent_resp = reflect(problem_nl = nl, domain = domain, past_reflections = reflections, experiential_agent_resp = experiential_agent_resp, evaluation = evaluation, model = REFLECTION_LLM_MODEL) # To do: improve
                reflection = reflection_agent_resp["reflection"]
                # pprint(reflection)
                # print()
            reflections.append(reflection)
            experiential_agent.reflections = reflections
    
    # Store result

def eval_exp(resume: bool, human_feedback: bool, max_trials = EXP_TESTING_TRIALS):
    if not resume:
        choice = input("Are you sure you want to restart the evaluation? Any progress will be lost (y/n):")
        if choice == "n" or choice == "N":
            return
    
    global experiential_agent
    print("⚙️ Loading dataset subsets...")
    try:
        train_dataset = load_planetarium_subset(TRAINING_SUBSET)
        test_dataset = load_planetarium_subset(TESTING_SUBSET)
        print("  ☑️ Loaded dataset subsets")
    except Exception as e:
        print("❌ Failed to load dataset subsets", e)

    print("⚙️ Selecting problems...")
    selected_cases = []
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][10:11]

    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="blocksworld"][0:3]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="gripper"][15:16]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][15:16]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][0:2]
    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="gripper"][0:2]
    # selected_cases += [ex for ex in test_dataset if ex["domain"]=="floor-tile"][0:2]

    # selected_cases += [ex for ex in train_dataset if ex["domain"]=="blocksworld"][121:122]

    # blocksworld_tasks = [ex for ex in test_dataset if ex["domain"]=="blocksworld"][:]
    # gripper_tasks = [ex for ex in test_dataset if ex["domain"]=="gripper"][:]
    # floor_tile_tasks = [ex for ex in test_dataset if ex["domain"]=="floor-tile"][:]
    
    # random.seed(42)
    # selected_cases = random.sample(blocksworld_tasks, 20)+random.sample(gripper_tasks, 20)+random.sample(floor_tile_tasks, 20)

    selected_cases = [ex for ex in test_dataset if ex["id"] in [109865, 164985, 165021, 165218, 165985, 166118, 166398, 167743, 20197, 20295]]

    cases = selected_cases
    seen_ids = []
    selected_cases = []
    for case in cases:
        if not case["id"] in seen_ids:
            selected_cases.append(case)
            seen_ids.append(case["id"])

    for task in selected_cases:
        print(get_task_short_desc(task))

    assert len(selected_cases) > 0

    # selected_cases[0]["natural_language"] = "The robot ArIel has 45 cubic pieces of wood, he gave them cute names: blo1, blo2, ..., blo45, and he put them one on top of the other until he had a single stack that reached the clouds, and he was left with no cubes in his hand. However, he does not like it because even though the stack is so tall, he does not know how to climb it. However, he knows how to go up a stair, but not how to build one. This is where you enter, you have built stairs before and start with a stack of size 1, then another of size 2, and so on. You have all the cubes at your disposal, help ArIel reach the sky!"
    # selected_cases[0]["natural_language"] = "You have only one block on the table. Leave it there."

    print(f"  ☑️  {len(selected_cases)} problems selected")

    # RESTART OR RESUME
    progress_path = os.path.join(BASE_DIR, "exp_evaluation_progress.json")
    if resume:
        progress = load_json_data(progress_path)
    else:
        progress = {
            "task_id": selected_cases[0]["id"],
            "ex_idx": 0
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)
    ex_idx_start = progress["ex_idx"]

    for i in range(ex_idx_start, len(selected_cases)):
        ex = selected_cases[i]
        idx = ex["id"]

        progress = {
            "task_id": idx,
            "ex_idx": i
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=4)

        domain = ex["domain"]
        nl = ex["natural_language"]
        pddl_gt = ex["problem_pddl"]

        experiential_agent.set_task(idx, domain, nl)

        reflections = []
        last_resp = {}

        print(f"\n🚀 Starting problem: {domain}_{idx}")
        print(get_task_short_desc(ex))
        print()
        
        dom_path = os.path.join(BASE_DIR, "domains", domain, "domain.pddl")
        case_dir = make_case_dir(RESULT_ROOT, "exp", domain, idx)
        trial_dict_path = os.path.join(RESULT_ROOT, "exp", "trials")
        os.makedirs(trial_dict_path, exist_ok=True)

        print("⏫ Storing natural language description and PDDL ground truth...")
        save_text(os.path.join(case_dir, "nl.txt"), nl)
        save_text(os.path.join(case_dir, "pddl_gt.pddl"), pddl_gt)
        print("  ☑️ Done")

        # Se puede hacer una sola vez por problema
        print("📐 Planning on ground truth...")
        plan_gt = generate_plan(dom_path, os.path.join(case_dir, "pddl_gt.pddl"))
        if plan_gt:
            save_text(os.path.join(case_dir, "plan_gt.txt"), plan_gt)
        print("  ☑️ Done")

        ################################################################
        for trial in range(max_trials): 
            print(f"Trial #{trial + 1}")
            print()
            experiential_agent.reflections = reflections
            trial_path = os.path.join(case_dir, f"trial_{trial + 1}")
            os.makedirs(trial_path, exist_ok=True)
            
            print("🤖 Generating prediction...")

            start_time = time.time()
            resp = experiential_agent.solve_task()
            generation_time = time.time() - start_time
            print(f"  ☑️ Done in {generation_time:.2f}s")

            prompt_tokens = resp["prompt_tokens"]
            completion_tokens = resp["completion_tokens"]
            total_tokens = resp["total_tokens"]
            print(f"  Used {prompt_tokens} tokens in prompt + {completion_tokens} tokens in completion = {total_tokens} = {sum(total_tokens)} tokens in total.")

            pddl_pred = resp["problem_pddl"]
            pddl_pred = get_pddl_substr(pddl_pred)
            pred_path = os.path.join(trial_path, f"pddl_pred.pddl")
            save_text(pred_path, pddl_pred)

            print("📋 Evaluating generated PDDL...")
            eval_result = eval_trial(ex, resp)
            evaluation = eval_result
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

            print("📐 Planning on generated PDDL...")
            if solvable:
                plan_pred = generate_plan(dom_path, pred_path)
                plan_gt = generate_plan(dom_path, os.path.join(trial_path, "pddl_gt.pddl"))
                if plan_pred:
                    save_text(os.path.join(trial_path, "plan_pred.txt"), plan_pred)
                print("  ☑️ Done")
            else:
                plan_pred = ""
                print("  ⏭️ Skipping predicted planning: not solvable")

            reflection_on_previous_trial = ""
            if trial > 0:
                reflection_on_previous_trial = reflections[-1]

            trial_dict = {
                "task": ex,
                "trial": trial + 1,
                "reflection_on_previous_trial": reflection_on_previous_trial,
                "plan_gt": plan_gt,
                "plan_pred": plan_pred,
                "eval": eval_result,
                "generation_time": generation_time
            }
            with open(os.path.join(trial_dict_path, f"{idx}_{trial + 1}.json"), "w", encoding="utf-8") as f:
                json.dump(trial_dict, f, indent=4)

            if eval_result["correct"]:
                break
            else:
                if trial == max_trials - 1:
                    break
                last_resp = resp
                last_resp["eval"] = evaluation
                experiential_agent.last_resp = last_resp
                if trial == max_trials - 2 and human_feedback: # only one trial remaining
                    print("TOO MANY FAILED ATTEMPTS. HUMAN FEEDBACK:")
                    reflection = input()
                else:
                    print("################## REFLECTION ##################")
                    reflection_agent_resp = reflect(problem_nl = nl, domain = domain, past_reflections = reflections, experiential_agent_resp = resp, evaluation = evaluation, model = REFLECTION_LLM_MODEL) # To do: improve
                    reflection = reflection_agent_resp["reflection"]
                    print("Reflection on failed attempt:")
                    pprint(reflection)
                reflections.append(reflection)
                experiential_agent.reflections = reflections
        
        print(f"🏁 Finished problem: {domain}_{idx}")

    print("  ☑️ Done")

    progress = {
        "done": "yes"
    }
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)
        
    print("\n🎉 Experiential agent evaluation complete.")

########### MAIN FUNCTIONS CALL ########### 

# run_evaluations(True)

# insights_extraction(False)

# eval_exp(False, False, 3)

# visualize_evaluation("evaluation_by_agent_2025-05-27_06-56-55.json")

####################################

def get_json_files(folder_path):
    """
    Returns a list of full paths to all JSON files in the specified folder.

    Parameters:
    folder_path (str): Path to the folder to search in.

    Returns:
    list: List of full file paths to JSON files.
    """
    # Initialize an empty list to store JSON file paths
    json_files = []

    # Loop through all items in the folder
    for filename in os.listdir(folder_path):
        # Check if the current file ends with '.json'
        if filename.lower().endswith('.json'):
            # Construct the full path to the file
            full_path = os.path.join(folder_path, filename)
            # Append the full path to the list
            json_files.append(full_path)

    return json_files

def show_token_consumption():
    total = 0
    count = 0
    total_tokens = []
    queries_files = get_json_files(os.path.join(BASE_DIR, "client", "queries"))
    for file in queries_files:
        query = load_json_data(file)
        if query is None:
            continue
        # print(query["total_tokens"])
        count += 1
        total += query["total_tokens"]
        total_tokens.append(query["total_tokens"])

    print(total)
    print(count)
    print(total / count)

def test(agent_names):
    for name in agent_names:
        print(name)
        parseable = 0
        solvable = 0
        correct = 0
        count = 0
        incorrect = []
        trials_files = get_json_files(os.path.join(BASE_DIR, "results", name, "trials"))
        d = {}
        for file in trials_files:
            trial = load_json_data(file)
            id = trial["task"]["id"]
            if id in d:
                eval = d[id]["eval"]
                if trial["eval"]["correct"] and not eval["correct"]:
                    d[id] = trial
                elif trial["eval"]["solvable"] and not eval["solvable"]:
                    d[id] = trial
                elif trial["eval"]["parseable"] and not eval["parseable"]:
                    d[id] = trial
            else:
                d[id] = trial
        # print(len(trials_files))
        for file in trials_files:
            trial = load_json_data(file)
            id = trial["task"]["id"]
            if d[id] != trial:
                continue
            # if not trial["task"]["id"] in [109865, 141761, 142306, 164985, 165021, 165028, 165218, 165985, 166118, 166172, 20097, 20197, 92243]:
            #     continue
            count += 1
            if trial["eval"]["parseable"]:
                parseable += 1
            if trial["eval"]["solvable"]:
                solvable += 1
            if trial["eval"]["correct"]:
                correct += 1
            else:
                incorrect.append(trial["task"]["id"])

            if trial["eval"]["init2_solvable"] and not trial["eval"]["goal2_solvable"]:
                print("WTFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                print(trial["task"]["id"])
            if trial["eval"]["goal2_solvable"] and not trial["eval"]["init2_solvable"]:
                print("KHEEEEEEEEEEEEEEEEEE")
                print(trial["task"]["id"])
        print(count, parseable, solvable, correct)
        # print(incorrect)
        print()

# active_agents = [
#     # "llm_planner", 
#     # "llm_planner_fsp", 
#     # "orig_llm_plus_p", 
#     "orig_llm_plus_p_fsp", 
#     "llm_plus_p", 
#     "llm_plus_p_fsp", 
#     # "gcd", 
#     # "daps_gcd", 
#     # "daps_gcd_r",
#     # "daps_gcd_fsp",
#     "daps_gcd_r_fsp",
#     "daps_gcd_r_fsp_i",
#     "r_fsp_i",
#     "exp"
# ]

# active_agents = [
#     "orig_llm_plus_p", 
#     "orig_llm_plus_p_fsp", 

#     "llm_plus_p",
#     "r",
#     "r_o",
#     # "r_o_gcd",
#     "r_o_daps_gcd",

#     "llm_plus_p_fsp",
#     "r_fsp",
#     "r_o_fsp",
#     # "r_o_gcd_fsp",
#     "r_o_daps_gcd_fsp",
    
#     "r_fsp_hi",
#     "r_o_daps_gcd_fsp_hi"
# ]

active_agents = [
    "orig_llm_plus_p", 
    "llm_plus_p",
    "r",
    "r_o",
    # "r_o_gcd",
    "r_o_daps_gcd",

    "orig_llm_plus_p_fsp", 
    "llm_plus_p_fsp",
    "r_fsp",
    "r_o_fsp",
    # "r_o_gcd_fsp",
    "r_o_daps_gcd_fsp",
    
    "r_fsp_hi",
    "r_o_daps_gcd_fsp_hi"
]

test(active_agents)

def trials_to_evaluation_by_agent(agent_names):
    evaluation_by_agent = {}
    for agent_name in agent_names:
        print(agent_name)
        evaluation_by_agent[agent_name] = {
            "name": agent_name,
            "parameters": {
                "llm_model": LLM_DEFAULT_MODEL
            },
            "domains": {
                "blocksworld": {
                    "name": "blocksworld",
                    "domain_pddl": "(define (domain blocksworld)\n\n  (:requirements :strips)\n\n  (:predicates\n    (clear ?x)\n    (on-table ?x)\n    (arm-empty)\n    (holding ?x)\n    (on ?x ?y)\n  )\n\n  (:action pickup\n    :parameters (?ob)\n    :precondition (and (clear ?ob) (on-table ?ob) (arm-empty))\n    :effect (and (holding ?ob) (not (clear ?ob)) (not (on-table ?ob))\n      (not (arm-empty)))\n  )\n\n  (:action putdown\n    :parameters (?ob)\n    :precondition (holding ?ob)\n    :effect (and (clear ?ob) (arm-empty) (on-table ?ob)\n      (not (holding ?ob)))\n  )\n\n  (:action stack\n    :parameters (?ob ?underob)\n    :precondition (and (clear ?underob) (holding ?ob))\n    :effect (and (arm-empty) (clear ?ob) (on ?ob ?underob)\n      (not (clear ?underob)) (not (holding ?ob)))\n  )\n\n  (:action unstack\n    :parameters (?ob ?underob)\n    :precondition (and (on ?ob ?underob) (clear ?ob) (arm-empty))\n    :effect (and (holding ?ob) (clear ?underob)\n      (not (on ?ob ?underob)) (not (clear ?ob)) (not (arm-empty)))\n  )\n)",
                    "problems": {}
                },
                "gripper": {
                    "name": "gripper",
                    "domain_pddl": "(define (domain gripper)\n  (:requirements :strips)\n  (:predicates\n    (room ?r)\n    (ball ?b)\n    (gripper ?g)\n    (at-robby ?r)\n    (at ?b ?r)\n    (free ?g)\n    (carry ?o ?g)\n  )\n\n  (:action move\n    :parameters (?from ?to)\n    :precondition (and (room ?from) (room ?to) (at-robby ?from))\n    :effect (and (at-robby ?to)\n      (not (at-robby ?from)))\n  )\n\n  (:action pick\n    :parameters (?obj ?room ?gripper)\n    :precondition (and (ball ?obj) (room ?room) (gripper ?gripper)\n      (at ?obj ?room) (at-robby ?room) (free ?gripper))\n    :effect (and (carry ?obj ?gripper)\n      (not (at ?obj ?room))\n      (not (free ?gripper)))\n  )\n\n  (:action drop\n    :parameters (?obj ?room ?gripper)\n    :precondition (and (ball ?obj) (room ?room) (gripper ?gripper)\n      (carry ?obj ?gripper) (at-robby ?room))\n    :effect (and (at ?obj ?room)\n      (free ?gripper)\n      (not (carry ?obj ?gripper)))\n  )\n)",
                    "problems": {}
                },
                "floor-tile": {
                    "name": "floor-tile",
                    "domain_pddl": "(define (domain floor-tile)\n  (:requirements :typing)\n  (:types\n    robot tile color - object\n  )\n\n  (:predicates\n    (robot-at ?r - robot ?x - tile)\n    (up ?x - tile ?y - tile)\n    (right ?x - tile ?y - tile)\n    (painted ?x - tile ?c - color)\n    (robot-has ?r - robot ?c - color)\n    (available-color ?c - color)\n  )\n\n  (:action change-color\n    :parameters (?r - robot ?c - color ?c2 - color)\n    :precondition (and (robot-has ?r ?c) (available-color ?c2))\n    :effect (and (not (robot-has ?r ?c)) (robot-has ?r ?c2)\n    )\n  )\n\n  (:action paint-up\n    :parameters (?r - robot ?y - tile ?x - tile ?c - color)\n    :precondition (and (robot-has ?r ?c) (robot-at ?r ?x) (up ?y ?x))\n    :effect  (painted ?y ?c)\n  )\n\n  (:action paint-down\n    :parameters (?r - robot ?y - tile ?x - tile ?c - color)\n    :precondition (and (robot-has ?r ?c) (robot-at ?r ?x) (up ?x ?y))\n    :effect (and (painted ?y ?c)\n    )\n  )\n\n  (:action paint-right\n    :parameters (?r - robot ?y - tile ?x - tile ?c - color)\n    :precondition (and (robot-has ?r ?c) (robot-at ?r ?x) (right ?y ?x))\n    :effect (and (painted ?y ?c)\n    )\n  )\n\n  (:action paint-left\n    :parameters (?r - robot ?y - tile ?x - tile ?c - color)\n    :precondition (and (robot-has ?r ?c) (robot-at ?r ?x) (right ?x ?y))\n    :effect (and (painted ?y ?c)\n    )\n  )\n\n  ; Robot movements\n  (:action up\n    :parameters (?r - robot ?x - tile ?y - tile)\n    :precondition (and (robot-at ?r ?x) (up ?y ?x))\n    :effect (and (robot-at ?r ?y) (not (robot-at ?r ?x)))\n  )\n\n  (:action down\n    :parameters (?r - robot ?x - tile ?y - tile)\n    :precondition (and (robot-at ?r ?x) (up ?x ?y))\n    :effect (and (robot-at ?r ?y) (not (robot-at ?r ?x)))\n  )\n\n  (:action right\n    :parameters (?r - robot ?x - tile ?y - tile)\n    :precondition (and (robot-at ?r ?x) (right ?y ?x))\n    :effect (and (robot-at ?r ?y) (not (robot-at ?r ?x)))\n  )\n\n  (:action left\n    :parameters (?r - robot ?x - tile ?y - tile)\n    :precondition (and (robot-at ?r ?x) (right ?x ?y))\n    :effect (and (robot-at ?r ?y) (not (robot-at ?r ?x)))\n  )\n\n)",
                    "problems": {}
                },
            }
        }
        trials_files = get_json_files(os.path.join(RESULT_ROOT, agent_name, "trials"))
        for file in trials_files:
            trial = load_json_data(file)
            domain = trial["task"]["domain"]
            id = trial["task"]["id"]
            _trial = {}
            for key in trial:
                if key == "task":
                    continue
                _trial[key] = trial[key]
            evaluation_by_agent[agent_name]["domains"][domain]["problems"][id] = {**trial["task"], **_trial}
        
    # print(evaluation_by_agent)
    # print()
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(RESULT_ROOT, f"evaluation_by_agent_{now}.json"), "w", encoding="utf-8") as f:
        json.dump(evaluation_by_agent, f, indent=4)
    
# trials_to_evaluation_by_agent(active_agents)