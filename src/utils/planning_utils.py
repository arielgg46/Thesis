from classical_planner.planner import generate_plan

def try_generate_plan(domain_file, problem_file, planner_path, work_dir):
    try:
        return generate_plan(domain_file, problem_file, planner_path, work_dir=work_dir)
    except Exception as e:
        print(f"❌ Error generating plan: {e}")
        return None
