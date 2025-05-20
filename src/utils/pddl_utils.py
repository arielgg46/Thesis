import re
from collections import defaultdict
from typing import List, Tuple

def get_pddl_substr(str):
    o, l, r = 0, -1, 0
    for i in range(len(str)):
        if str[i] == '(':
            if l == -1:
                l = i
            o += 1
        elif str[i] == ')':
            o -= 1
            if o == 0:
              r = i
              return str[l:r+1]
    return str

def extract_typed_objects(pddl: str) -> List[Tuple[str, List[str]]]:
    """
    Extrae objetos y sus tipos desde la sección (:objects ...) de un problema PDDL.
    Si un objeto no tiene tipo declarado, se asume que es del tipo "object".
    
    Retorna una lista de pares (tipo, [objetos]), agrupando correctamente aunque los objetos
    de un mismo tipo estén separados.
    """
    match = re.search(r'\(:objects(.*?)\)', pddl, re.S)
    if not match:
        return {}

    section = match.group(1)
    tokens = section.split()

    type_to_objects = defaultdict(list)
    seen_types_order = []
    untyped_objects = []

    current_objects = []

    i = 0
    while i < len(tokens):
        if tokens[i] == "-":
            # Assign collected objects to the type
            t = tokens[i + 1]
            if t not in type_to_objects:
                seen_types_order.append(t)
            type_to_objects[t].extend(current_objects)
            current_objects = []
            i += 2
        else:
            current_objects.append(tokens[i])
            i += 1

    # Any objects left in buffer are untyped
    for obj in current_objects:
        untyped_objects.append(obj)

    if untyped_objects:
        if "object" not in type_to_objects:
            seen_types_order.append("object")
        type_to_objects["object"].extend(untyped_objects)

    # Ensure uniqueness within each type
    # result = [(t, list(dict.fromkeys(type_to_objects[t]))) for t in seen_types_order]
    return type_to_objects

def split_pddl_problem_sections(pddl: str) -> dict:
    """
    Dado un string PDDL de problema, devuelve un diccionario con las partes:
    prefix, init, middle, goal, suffix.
    """
    # Buscar la apertura de (:init
    init_start = re.search(r':init', pddl)
    if not init_start:
        raise ValueError("No se encontró sección :init en el problema.")

    # Buscar la apertura de (:goal
    goal_start = re.search(r':goal', pddl)
    if not goal_start:
        raise ValueError("No se encontró sección :goal en el problema.")
    
    # Encontrar el primer predicado después de :init
    init_predicates_start = pddl.find("(", init_start.end())

    # Encontrar (and dentro de :goal
    and_match = re.search(r'and', pddl[goal_start.end():])
    if not and_match:
        raise ValueError("No se encontró (and dentro de :goal.")
    and_start_abs = goal_start.end() + and_match.start()

    # El primer predicado dentro de (and
    goal_predicates_start = pddl.find("(", and_start_abs + len("(and"))

    if goal_predicates_start == -1:
        raise ValueError("No se encontraron predicados dentro de goal.")

    # Cortar prefix e init
    prefix = pddl[:init_predicates_start]
    rest_after_prefix = pddl[init_predicates_start:goal_start.start()]
    middle_start = rest_after_prefix.rfind(")") + init_predicates_start
    init_content = pddl[init_predicates_start:middle_start].strip()
    middle = pddl[middle_start:goal_predicates_start].rstrip()

    # Ahora en rest_after_middle vamos a contar paréntesis
    rest_after_middle = pddl[goal_predicates_start:]
    
    parens_balance = 1
    goal_end_idx = None
    for idx, char in enumerate(rest_after_middle):
        if char == '(':
            parens_balance += 1
        elif char == ')':
            parens_balance -= 1

        if parens_balance == 0 and idx > 0:
            goal_end_idx = idx
            break

    if goal_end_idx is None:
        raise ValueError("No se pudo encontrar el final de la sección goal balanceando paréntesis.")

    goal_content = rest_after_middle[:goal_end_idx].strip()
    suffix = rest_after_middle[goal_end_idx:].strip()

    return prefix, init_content, middle, goal_content, suffix
    # return {
    #     "prefix": prefix,
    #     "init": init_content,
    #     "middle": middle,
    #     "goal": goal_content,
    #     "suffix": suffix
    # }