import os

def get_domain_path(domain):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dom_path = os.path.join(BASE_DIR, domain, "domain.pddl")
    return dom_path

def get_domain_pddl(domain):
    dom_path = get_domain_path(domain)
    with open(dom_path, encoding="utf-8") as f:
        domain_pddl = f.read()
    return domain_pddl

def get_domain_description(domain):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dom_path = os.path.join(BASE_DIR, domain, "domain_description.txt")
    with open(dom_path, encoding="utf-8") as f:
        domain_description = f.read()
    return domain_description

def get_domain_requirements(domain):
    if domain == "floor-tile":
        return "STRIPS + :typing"
    else:
        return "STRIPS"

def get_actions_description(domain):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dom_path = os.path.join(BASE_DIR, domain, "actions_description.txt")
    with open(dom_path, encoding="utf-8") as f:
        actions_description = f.read()
    return actions_description

def get_planner_output_syntax(domain):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dom_path = os.path.join(BASE_DIR, domain, "planner_output_syntax.txt")
    with open(dom_path, encoding="utf-8") as f:
        planner_output_syntax = f.read()
    return planner_output_syntax

def get_fsp_example(domain):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    domain_folder_path = os.path.join(BASE_DIR, domain)
    nl_path = os.path.join(domain_folder_path, "fsp_ex_nl.txt")
    pddl_path = os.path.join(domain_folder_path, "fsp_ex_pddl.pddl")
    plan_path = os.path.join(domain_folder_path, "fsp_ex_plan.pddl")
    objects_path = os.path.join(domain_folder_path, "fsp_ex_objects.json")
    reasoning_path = os.path.join(domain_folder_path, "fsp_ex_reasoning.txt")

    with open(nl_path, encoding="utf-8") as f:
        nl = f.read()
    with open(pddl_path, encoding="utf-8") as f:
        pddl = f.read()
    with open(plan_path, encoding="utf-8") as f:
        plan = f.read()
    with open(objects_path, encoding="utf-8") as f:
        objects = f.read()
    with open(reasoning_path, encoding="utf-8") as f:
        reasoning = f.read()

    return nl, pddl, plan, objects, reasoning

def get_domain_predicates(domain):
    if domain == "blocksworld":
        return [
            ("clear", 1),
            ("on-table", 1),
            ("arm-empty", 0),
            ("holding", 1),
            ("on", 2)
        ]
    if domain == "gripper":
        return [
            ("room", 1),
            ("ball", 1),
            ("gripper", 1),
            ("at-robby", 1),
            ("at", 2),
            ("free", 1),
            ("carry", 2)
        ]
    if domain == "floor-tile":
        return [
            ("robot-at", ["robot", "tile"]),
            ("up", ["tile", "tile"]),
            ("right", ["tile", "tile"]),
            ("painted", ["tile", "color"]),
            ("robot-has", ["robot", "color"]),
            ("available-color", ["color"])
        ]
        # [
        #     ("robot-at", 2),
        #     ("up", 2),
        #     ("right", 2),
        #     ("painted", 2),
        #     ("robot-has", 2),
        #     ("available-color", 1)
        # ]
        
        
def get_domain_types(domain: str):
    """
    Retorna un diccionario de tipo : tipo_del_que_hereda
    """
    if domain == "blocksworld":
        return {}
    if domain == "gripper":
        return {}
    if domain == "floor-tile":
        return {
            "robot": "object",
            "tile": "object",
            "color": "object"
        }