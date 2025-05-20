import json
from typing import List

from client.client import llm_query
from grammar.grammar import get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing, get_typed_objects_grammar, get_not_typed_objects_grammar
from domains.utils import get_domain_pddl, get_domain_predicates, get_domain_types, get_domain_description, get_domain_requirements

def get_fsp_str(fsp_examples: List[dict], fields: List[str]) -> str:
    """
    Returns the Few-Shot Prompting part of the prompt given
    few-shot examples, and the fields of the examples to include
    """
    fsp_str = ""
    for i in range(len(fsp_examples)):
        fsp_ex = fsp_examples[i]
        if i > 0:
            fsp_str += "\n"
        else:
            fsp_str += "\n\n"
        fsp_str += f"Example #{i+1}:"
        for j in range(len(fields)):
            field = fields[j]
            field_preffix = {
                "nl": "Problem",
                "reasoning": "Reasoning",
                "objects": "Objects to use",
                "pddl": "Problem PDDL"
            }
            fsp_str += "\n"
            if j > 0:
                fsp_str += "\n"
            fsp_str += f"{field_preffix[field]}:\n{fsp_ex[field]}"
    return fsp_str

def get_reflections_str(reflections: List[str]) -> str:
    """
    Returns the Past trials reflections part of the prompt given
    the reflections on the past trials
    """
    reflections_str = ""
    if len(reflections) > 0:
        reflections_str = "\nYou have tried the problem before, unsuccesfully. Reflections on previous trials:"
    for reflection in reflections:
        reflections_str += f"\n- {reflection}"
    if len(reflections) > 0:
        reflections_str += "\n"
    
    return reflections_str

def get_reflections_str(last_resp: dict, reflections: List[str]) -> str:
    """
    Returns the Past trials reflections part of the prompt given
    the reflections on the past trials
    """
    reflections_str = ""
    if len(reflections) > 0:
        reflections_str = f"""
You have tried the problem before, unsuccesfully. This was your answer:
Objects to use:
{last_resp["objects"]}

Problem PDDL:
{last_resp["problem_pddl"]}

Reflection on the previous trial:
{reflections[-1]}
"""
    
    return reflections_str

def get_problem_objects(problem_nl: str, 
                     domain: str, 
                     reflections: List[str],
                     fsp_examples: List[dict],
                     model: str):
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    not_typed_objects_grammar = get_not_typed_objects_grammar()

    fsp_str = get_fsp_str(fsp_examples = fsp_examples, fields = ["nl", "reasoning", "objects"])
    # reflections_str = get_reflections_str(last_resp =  reflections = reflections)

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain.
Provide a list of all the objects in the PDDL problem instance.{fsp_str}"""
    
    user_prompt = f"""New problem:
{problem_nl}
Objects to use:
"""
# {reflections_str}

    chat_completion = llm_query(system_prompt, user_prompt, model, not_typed_objects_grammar)

    return chat_completion

def get_problem_typed_objects(problem_nl: str, 
                     domain: str,
                     reflections: List[str],
                     fsp_examples: List[dict],
                     model: str):
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    domain_types = []
    domain_types_dict = get_domain_types(domain)
    for type in domain_types_dict:
        domain_types.append(type)
    
    if domain_types == []:
        pass
    # domain_types.append("object")

    typed_objects_grammar = get_typed_objects_grammar(domain_types)

    # reflections_str = get_reflections_str(reflections = reflections)
    fsp_str = get_fsp_str(fsp_examples = fsp_examples, fields = ["nl", "objects"])

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Object types: 
{domain_types}

Task:
You will be given natural language descriptions of planning problems in this domain.
Provide a list of all the objects in the PDDL problem instance, separated by type.{fsp_str}"""
    
    user_prompt = f"""New problem:
{problem_nl}
Objects to use:
"""
# {reflections_str}

    chat_completion = llm_query(system_prompt, user_prompt, model, typed_objects_grammar)
    
    return chat_completion

def get_problem_reasoning(
    problem_nl: str,
    domain: str,
    fsp_examples: List[dict],
    reasoning_model: str,
    max_reasoning_tokens: int = 500,
) -> str:
    
    domain_pddl = get_domain_pddl(domain)
    domain_description = get_domain_description(domain)

    fsp_str = get_fsp_str(fsp_examples = fsp_examples, fields = ["nl", "reasoning"])

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You are an advanced planning modeling reasoning agent. When given the planning domain and a natural language description of a problem in this domain, you will *reason step by step* to resolve any ambiguities or missing details, to help to improve the semantic correctness of a posterior problem PDDL generation by another model.
Write your reasoning as exactly 3 paragraphs of no more than 100 words each. In them you should cover, in order:

1. **Objects**: list every object by name.  
2. **Initial state**: describe the initial state, and any assumptions you make to fill in missing info.  
3. **Goal state**: describe the goal state, and any assumptions you make to fill in missing info.

Fully specify the subgoals and initial state as detailed as you can. Don't reason about the planning itself, just the PDDL. Don't extend beyond 3 short paragraphs.{fsp_str}
"""
    
    user_prompt = f"""New problem:
{problem_nl}

Reasoning:
"""

    chat_completion = llm_query(system_prompt, user_prompt, reasoning_model)

    return chat_completion


# LLM+P with Domain-and-Problem-specific Grammar Constrained Decoding (constraints over predicates, types and objects), reasoning, objects extraction, Few-Shot Prompting with RAG, and Past trials reflections
def solve_task(problem_nl: str, 
                domain: str,  
                last_resp: dict,
                reflections: List[str],
                fsp_examples: List[dict],
                model: str) -> dict:
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    domain_predicates = get_domain_predicates(domain)
    domain_types = get_domain_types(domain)
    requirements = get_domain_requirements(domain)
    
    # Objects
    # objects_str = ""
    if domain_types == {}:
        objects_resp = get_problem_objects(problem_nl, domain, reflections, fsp_examples, model)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        objects = objects_dict["objects"]
        pddl_problem_grammar = get_pddl_problem_grammar_daps_no_typing(domain, domain + "_problem", domain_predicates, objects)
    else:
        objects_resp = get_problem_typed_objects(problem_nl, domain, reflections, fsp_examples, model)
        # print(objects_resp.choices[0].message.content)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        # print(objects_dict)
        objects = []
        for type in objects_dict:
            objects.append((type, objects_dict[type]))
        pddl_problem_grammar = get_pddl_problem_grammar_daps_typing(domain, domain + "_problem", domain_predicates, objects, domain_types)

    # Few-shot Prompting
    fsp_str = get_fsp_str(fsp_examples = fsp_examples, fields = ["nl", "objects", "pddl"])
    
    # Reflections on previous trials
    reflections_str = get_reflections_str(last_resp = last_resp, reflections = reflections)
    print(reflections_str)

    # System Prompt
    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain. 
Provide the problem PDDL (that conforms to the grammar of the {requirements} subset of PDDL) of this problem.{fsp_str}
"""
    
    # User Prompt
    user_prompt = f"""New problem:
{problem_nl}

Objects to use:
{objects}
{reflections_str}
Problem PDDL:
"""

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model, pddl_problem_grammar)
    
    # Response
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        # "objects_resp" : objects_resp.choices[0].message.content,
        "objects" : objects,
        "problem_pddl" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [objects_resp.usage.prompt_tokens, chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [objects_resp.usage.completion_tokens, chat_completion.usage.completion_tokens], 
        "total_tokens" : [objects_resp.usage.total_tokens, chat_completion.usage.total_tokens, objects_resp.usage.total_tokens + chat_completion.usage.total_tokens]
    }
    return response