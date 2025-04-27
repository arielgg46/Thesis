import json
from utils.client import make_fw_client
from grammar.grammar import get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing, get_typed_objects_grammar, get_not_typed_objects_grammar
from domains.utils import get_domain_pddl, get_domain_predicates, get_domain_types, get_domain_description, get_domain_requirements

def get_problem_objects(problem_nl: str, 
                     domain: str, 
                     api_key: str, 
                     model: str):
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    not_typed_objects_grammar = get_not_typed_objects_grammar()

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain.
Provide a list of all the objects in the PDDL problem instance.
"""
    user_prompt = f"""Problem:
{problem_nl}

Objects:
"""

    client = make_fw_client(api_key)
    chat_completion = client.chat.completions.create(
        model=model,
        response_format={"type": "grammar", "grammar": not_typed_objects_grammar},
        messages=[
            {"role": "system", "content": system_prompt,},
            {"role": "user", "content": user_prompt},
        ]
    )

    return chat_completion

def get_problem_typed_objects(problem_nl: str, 
                     domain: str, 
                     api_key: str, 
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

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Object types: 
{domain_types}

Task:
You will be given natural language descriptions of planning problems in this domain.
Provide a list of all the objects in the PDDL problem instance, separated by type.
"""
    
    user_prompt = f"""Problem:
{problem_nl}

Objects:
"""

    client = make_fw_client(api_key)
    chat_completion = client.chat.completions.create(
        model=model,
        response_format={"type": "grammar", "grammar": typed_objects_grammar},
        messages=[
            {"role": "system", "content": system_prompt,},
            {"role": "user", "content": user_prompt},
        ]
    )
    
    return chat_completion

# LLM+P with Domain-and-Problem-specific Grammar Constrained Decoding (constraints over predicates, types and objects)
def get_problem_pddl_daps_gcd(problem_nl: str, 
                     domain: str, 
                     api_key: str, 
                     model: str):
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    domain_predicates = get_domain_predicates(domain)
    domain_types = get_domain_types(domain)
    requirements = get_domain_requirements(domain)

    objects_str = ""
    if domain_types == {}:
        objects_resp = get_problem_objects(problem_nl, domain, api_key, model)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        objects = objects_dict["objects"]
        pddl_problem_grammar = get_pddl_problem_grammar_daps_no_typing(domain, domain + "_problem", domain_predicates, objects)
    else:
        objects_resp = get_problem_typed_objects(problem_nl, domain, api_key, model)
        print(objects_resp.choices[0].message.content)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        print(objects_dict)
        objects = []
        for type in objects_dict:
            objects.append((type, objects_dict[type]))
        pddl_problem_grammar = get_pddl_problem_grammar_daps_typing(domain, domain + "_problem", domain_predicates, objects, domain_types)

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain. 
Provide the problem PDDL (that conforms to the grammar of the {requirements} subset of PDDL) of this problem.
"""
    
    user_prompt = f"""Problem:
{problem_nl}

Objects to use:
{objects}

Problem PDDL:
"""

    client = make_fw_client(api_key)
    chat_completion = client.chat.completions.create(
        model=model,
        response_format={"type": "grammar", "grammar": pddl_problem_grammar},
        messages=[
            {"role": "system", "content": system_prompt,},
            {"role": "user", "content": user_prompt},
        ]
    )
    
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "objects_resp" : objects_resp.choices[0].message.content,
        "objects" : objects,
        "problem_pddl" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [objects_resp.usage.prompt_tokens, chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [objects_resp.usage.completion_tokens, chat_completion.usage.completion_tokens], 
        "total_tokens" : [objects_resp.usage.total_tokens, chat_completion.usage.total_tokens, objects_resp.usage.total_tokens + chat_completion.usage.total_tokens]
    }
    return response