import subprocess
import os
import shutil

def generate_plan(domain_file: str,
                  problem_file: str,
                  fast_downward_path: str,
                  alias: str = "lama-first",
                  work_dir: str = None,
                  verbose: bool = False) -> str:
    """
    Runs Fast Downward with the specified domain and problem files.
    - domain_file and problem_file should be absolute paths.
    - work_dir: directory where the plan file ('sas_plan') is expected to be created.
    Returns: the plan as a string.
    """
    cwd = work_dir or os.getcwd()
    cmd = [
        "python",
        os.path.join(fast_downward_path, "fast-downward.py"),
        "--alias", alias,
        domain_file,
        problem_file,
    ]
    # Run the command in the specified working directory
    proc = subprocess.run(cmd, cwd=cwd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True)
    
    if verbose:
        print("==== Fast Downward STDOUT ====")
        print(proc.stdout)
        print("==== Fast Downward STDERR ====")
        print(proc.stderr)

    sas_plan = os.path.join(cwd, "sas_plan")
    if not os.path.exists(sas_plan):
        raise FileNotFoundError(f"'sas_plan' not found in {cwd}")

    with open(sas_plan, "r", encoding="utf-8") as f:
        plan = f.read()

    os.remove(sas_plan)
    
    return plan
