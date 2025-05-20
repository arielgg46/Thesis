import json
from typing import List

from client.client import llm_query
from domains.utils import get_domain_pddl, get_domain_description

def reflect(problem_nl: str, 
            domain: str, 
            past_reflections: List[str], # don't know if I will use them
            modeling_agent_resp: dict, 
            evaluation: dict,
            api_key: str, 
            model: str) -> dict:
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    
    # System Prompt
    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given the natural language description of a planning problem in this domain, and a failed atempt of a modeling agent to generate the problem PDDL of this description.
Provide a single paragraph reflection on what could be wrong with the failed atempt, and how to correct it.
Think if it is really necessary to change anything on the initial state, goal state, or both, and what.
Take into account that the set of predicates in the previous atempt may be incorrect, or may be correct but could be missing others to fully specify the initial and goal states.
""" # To do: improve prompt (better custom formatting and language)
    
    # User Prompt
    user_prompt = f"""Problem:
{problem_nl}

Modeling agent's failed atempt:
Determined objects to use:
{modeling_agent_resp["objects"]}

Generated problem PDDL:
{modeling_agent_resp["problem_pddl"]}

Evaluation feedback:
{evaluation}

Your reflection:
""" # To do: improve prompt (better custom formatting and language)

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model)
    
    # Response
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "reflection" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response