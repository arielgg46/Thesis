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
        return []

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