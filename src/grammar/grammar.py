from typing import List, Dict, Tuple

def get_predicate_arity_str(predicate: str, arity: int) -> str:
  if arity == 0:
    return f'"(" "{predicate}" ")"'
  return f'"(" "{predicate}" (ws object){"{"}{arity}{"}"} ")"'

def get_pddl_problem_grammar(domain, problem, predicates = None, objects = None):
  object_rhs = "name"
  if objects is not None:
    object_rhs = f'"{objects[0]}"'
    for obj in objects[1:]:
      object_rhs += f' | "{obj}"'

  atomic_formula_rhs = '"(" name (ws object)* ")"'
  if predicates is not None:
    atomic_formula_rhs = get_predicate_arity_str(predicates[0][0], predicates[0][1])
    for predicate,arity in predicates[1:]:
      atomic_formula_rhs += " | " + get_predicate_arity_str(predicate, arity)

  requirements = '":strips"'
  typed_list_rhs = '(name ws)*'
  if domain in ['tile-world']:
    requirements = '":strips :typing"'
    typed_list_rhs = '(name ws)* | ((name ws)+ "-" ws type ws)+'

  return f"""root ::= define
define ::= "(" ws "define" ws problemDecl domainDecl requireDef objectDecl init goal ")"

problemDecl ::= "(" ws "problem" ws "{problem}" ws ")" ws
domainDecl ::= "(" ws ":domain" ws "{domain}" ws ")" ws
objectDecl ::= "(" ws ":objects" ws typedList ws ")" ws
requireDef ::= "(" ws ":requirements" ws {requirements} ws ")" ws
init ::= "(" ws ":init" ws initEl* ")" ws
initEl ::= literal
goal ::= "(" ws ":goal" ws preGD ")" ws

typedList ::= {typed_list_rhs}
type ::= "(either" primitiveType+ ")" | primitiveType
primitiveType ::= name | "object"

literal ::= atomicFormula ws | "(not " atomicFormula ")" ws
atomicFormula ::= {atomic_formula_rhs}

preGD ::= "(and" ws GD+ ")" | GD
GD ::= atomicFormula ws

object ::= {object_rhs}
name ::= letter anyChar*
letter ::= [a-zA-Z]
anyChar ::= letter | digit | "-" | "_"

number ::= digit+ decimal?
digit ::= [0-9]
decimal ::= "." digit+

ws ::= [ \t\n]*
"""

def get_pddl_problem_grammar_daps_no_typing(domain: str, problem: str, predicates: List[Tuple[str, int]], objects: List[str]) -> str:
  object_rhs = f'"{objects[0]}"'
  objects_def = f'{objects[0]}'
  for obj in objects[1:]:
    object_rhs += f' | "{obj}"'
    objects_def += f' {obj}'

  atomic_formula_rhs = get_predicate_arity_str(predicates[0][0], predicates[0][1])
  for predicate,arity in predicates[1:]:
    atomic_formula_rhs += " | " + get_predicate_arity_str(predicate, arity)

  return f"""root ::= define
define ::= "(" ws "define" ws problemDecl domainDecl requireDef objectDecl init goal ")"

problemDecl ::= "(" ws "problem" ws "{problem}" ws ")" ws
domainDecl ::= "(" ws ":domain" ws "{domain}" ws ")" ws
objectDecl ::= "(" ws ":objects" ws "{objects_def}" ws ")" ws
requireDef ::= "(" ws ":requirements" ws ":strips" ws ")" ws
init ::= "(" ws ":init" ws initEl* ")" ws
initEl ::= literal
goal ::= "(" ws ":goal" ws preGD ")" ws

literal ::= atomicFormula ws | "(not " atomicFormula ")" ws
atomicFormula ::= {atomic_formula_rhs}

preGD ::= "(and" ws GD+ ")" | GD
GD ::= atomicFormula ws

object ::= {object_rhs}
ws ::= [ \t\n]*
"""

def get_pddl_problem_grammar_daps_typing(domain: str, problem: str, predicates: List[Tuple[str, List[str]]], objects: List[Tuple[str, List[str]]], types: Dict[str, str]) -> str:
  object_rhs = {"object": ""}
  for type in types:
    object_rhs[type] = ""
  
  objects_def = ""
  for type, obj_list in objects:
    for obj in obj_list:
      objects_def += f"{obj} "
      cur_type = type
      while True:
        if object_rhs[cur_type] != "":
          object_rhs[cur_type] += " | "
        object_rhs[cur_type] += f'"{obj}"'
        if cur_type == "object":
          break
        cur_type = types[cur_type]

    objects_def += f"- {type} "
  
  objects_productions = ""
  for type in object_rhs:
    rhs = object_rhs[type]
    objects_productions += f"obj-{type} ::= {rhs}\n"

  atomic_formula_rhs = ""
  for predicate,arg_types in predicates:
    if atomic_formula_rhs != "":
      atomic_formula_rhs += " | "
    atomic_formula_rhs += f'"({predicate}"'
    for arg_type in arg_types:
      atomic_formula_rhs += f" ws obj-{arg_type}"
    atomic_formula_rhs += f' ws ")"'
    
  return f"""root ::= define
define ::= "(" ws "define" ws problemDecl domainDecl requireDef objectDecl init goal ")"

problemDecl ::= "(" ws "problem" ws "{problem}" ws ")" ws
domainDecl ::= "(" ws ":domain" ws "{domain}" ws ")" ws
objectDecl ::= "(" ws ":objects" ws "{objects_def}" ws ")" ws
requireDef ::= "(" ws ":requirements" ws ":strips :typing" ws ")" ws
init ::= "(" ws ":init" ws initEl* ")" ws
initEl ::= literal
goal ::= "(" ws ":goal" ws preGD ")" ws

literal ::= atomicFormula ws | "(not " atomicFormula ")" ws
atomicFormula ::= {atomic_formula_rhs}

preGD ::= "(and" ws GD+ ")" | GD
GD ::= atomicFormula ws

{objects_productions}
ws ::= [ \t\n]*
"""

def get_typed_objects_grammar(types):
  objects_dict = '"{\n"'
  first = True
  for type in types:
    if first:
      first = False
    else:
      objects_dict += ' "," el '
    objects_dict += f'tab dq "{type}" dq ":" obj-list'
  objects_dict += ' "\n}"'
  
  return f"""root ::= {objects_dict}
obj-list ::= "[" obj (", " obj)* "]"
obj ::= dq letter anyChar* dq

letter ::= [a-zA-Z]
anyChar ::= letter | digit | "-" | "_"
digit ::= [0-9]

tab ::= "\t"
dq ::= "\\\""
el ::= "\n"
"""

def get_not_typed_objects_grammar():
  return """root ::= "{" dq "objects" dq ": [" obj (", " obj)* "]" "}"
obj ::= dq letter anyChar* dq

letter ::= [a-zA-Z]
anyChar ::= letter | digit | "-" | "_"
digit ::= [0-9]
dq ::= "\\\""
"""