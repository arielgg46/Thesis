import os
import subprocess

def validate_plan(
    domain_file: str,
    problem_file: str,
    plan_file: str,
    val_binary: str = "validate",   # ejecutable VAL, o ruta absoluta
    work_dir: str = None,
    verbose: bool = False
) -> bool:
    """
    Valida un plan existente usando el validador VAL.
    
    Parámetros:
    - domain_file: ruta al PDDL de dominio.
    - problem_file: ruta al PDDL de problema.
    - plan_file: ruta al archivo de plan (sas_plan, plan.txt, etc.).
    - val_binary: nombre o ruta al binario 'validate' de VAL.
    - work_dir: directorio de trabajo donde ejecutar el comando.
    - verbose: muestra stdout/stderr del validador.

    Retorna:
    - True si VAL retorna exit code 0 (plan válido).
    - False en cualquier otro caso.
    """
    cwd = work_dir or os.getcwd()
    # Asegurarse de que estamos en el directorio correcto (opcional)
    os.makedirs(cwd, exist_ok=True)

    # Comando VAL: validate domain.pddl problem.pddl plan_file
    cmd = [
        val_binary,
        domain_file,
        problem_file,
        plan_file
    ]

    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if verbose:
        print("==== VAL STDOUT ====")
        print(proc.stdout)
        print("==== VAL STDERR ====")
        print(proc.stderr)

    if "Failed" in proc.stdout:
        return False

    return proc.returncode == 0




# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAST_DOWNWARD_PATH = r"D:\fast-downward-24.06.1"
VAL_PATH = r"C:\Tools\Val-20211204.1-win64\bin\Validate.exe"

problem_file = os.path.join(BASE_DIR, "pddl_gt.pddl")
domain_file = os.path.join(BASE_DIR, "domain.pddl")
plan_file = os.path.join(BASE_DIR, "plan_gt.txt")

is_valid = validate_plan(
    domain_file=domain_file,
    problem_file=problem_file,
    plan_file=plan_file,
    val_binary=VAL_PATH,
    work_dir=BASE_DIR,
    verbose=False
)

print(is_valid)

