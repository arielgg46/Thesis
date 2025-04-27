import json
from utils.client import make_fw_client
from grammar.grammar import get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing, get_typed_objects_grammar, get_not_typed_objects_grammar
from domains.utils import get_domain_pddl, get_domain_predicates, get_domain_types, get_domain_description, get_domain_requirements

def get_problem_objects(problem_nl: str, 
    domain: str, 
    reasoning: str,
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

Reasoning:
{reasoning}

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
    reasoning: str,
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

Reasoning:
{reasoning}

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

def get_problem_reasoning(
    problem_nl: str,
    domain: str,
    api_key: str,
    reasoning_model: str,
    max_reasoning_tokens: int = 500,
) -> str:
    
    domain_pddl = get_domain_pddl(domain)
    domain_description = get_domain_description(domain)

    client = make_fw_client(api_key)
    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You are an expert AI modeler. When given a natural language problem description and the domain, you will first *reason step by step* to resolve any ambiguities or missing details, to help to improve the semantic correctness of a posterior problem PDDL generation by another model.
Write your reasoning as exactly 3 paragraphs of no more than 100 words each. In them you should cover, in order:

1. **Objects**: list every object by name.  
2. **Initial state**: describe how they are arranged, and any assumptions you make to fill in missing info.  
3. **Goal state**: describe the desired arrangement, and any assumptions you make.

Fully specify the subgoals and initial state as detailed as you can. Don't reason about the planning itself, just the PDDL. Don't extend beyond 3 short paragraphs.
"""
    
    user_prompt = f"""Problem:
{problem_nl}

Reasoning:
"""

    resp = client.chat.completions.create(
        model=reasoning_model,
        # max_tokens=max_reasoning_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    return resp


def get_problem_pddl_daps_gcd_reasoning(
    problem_nl: str,
    domain: str,
    api_key: str,
    gcd_model: str,
    reasoning_model: str,
    max_reasoning_tokens: int = 500) -> dict:
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    domain_predicates = get_domain_predicates(domain)
    domain_types = get_domain_types(domain)
    requirements = get_domain_requirements(domain)

    # 1) Reasoning
    reasoning_resp = get_problem_reasoning(
        problem_nl, domain, api_key,
        reasoning_model, max_reasoning_tokens
    )
    reasoning = reasoning_resp.choices[0].message.content.strip()

    # 2) Objects
    if domain_types == {}:
        objects_resp = get_problem_objects(problem_nl, domain, reasoning, api_key, gcd_model)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        objects = objects_dict["objects"]
        pddl_problem_grammar = get_pddl_problem_grammar_daps_no_typing(domain, domain + "_problem", domain_predicates, objects)
    else:
        objects_resp = get_problem_typed_objects(problem_nl, domain, reasoning, api_key, gcd_model)

        # Add try-catch
        objects_dict = json.loads(objects_resp.choices[0].message.content)
        objects = []
        for type in objects_dict:
            objects.append((type, objects_dict[type]))
        pddl_problem_grammar = get_pddl_problem_grammar_daps_typing(domain, domain + "_problem", domain_predicates, objects, domain_types)

    # 3) PDDL
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

Reasoning: 
{reasoning}

Objects to use:
{objects}

Problem PDDL:
"""

    client = make_fw_client(api_key)
    chat_completion = client.chat.completions.create(
        model=gcd_model,
        response_format={"type": "grammar", "grammar": pddl_problem_grammar},
        messages=[
            {"role": "system", "content": system_prompt,},
            {"role": "user", "content": user_prompt},
        ]
    )
    
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "reasoning": reasoning,
        "objects_resp" : objects_resp.choices[0].message.content,
        "objects" : objects,
        "problem_pddl" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [reasoning_resp.usage.prompt_tokens, objects_resp.usage.prompt_tokens, chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [reasoning_resp.usage.completion_tokens, objects_resp.usage.completion_tokens, chat_completion.usage.completion_tokens],
        "total_tokens" : [reasoning_resp.usage.total_tokens, objects_resp.usage.total_tokens, chat_completion.usage.total_tokens, reasoning_resp.usage.total_tokens + objects_resp.usage.total_tokens + chat_completion.usage.total_tokens]
    }
    return response