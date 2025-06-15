import json
from typing import List

from client.client import llm_query
from domains.utils import get_domain_pddl, get_domain_description

def get_domain_requirements(domain):
    if domain == "floor-tile":
        return ":strips + :typing"
    else:
        return ":strips"

def get_feedback_str(eval):
    feedback_str = ""
    for fb in eval["feedback"]:
        if feedback_str != "":
            feedback_str += "\n"
        feedback_str += f"- {fb}"
    return feedback_str

def reflect(problem_nl: str, 
            domain: str, 
            past_reflections: List[str], # don't know if I will use them
            experiential_agent_resp: dict, 
            evaluation: dict,
            model: str) -> dict:
    
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)

    requirements = get_domain_requirements(domain)
    
    # System Prompt
    system_prompt = f"""You are an advanced Planning Modeler AI Agent, capable of reflecting on failed attempts of planning problems within a given domain. In each case, a modeler agent was provided with the domain description, its corresponding PDDL file, and a natural language description of the problem, then attempted to generate the Problem PDDL file.

Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be presented with a natural language description of a planning problem, along with a failed attempt to generate its corresponding PDDL representation. You will also receive a description of the errors in the attempted PDDL. The generated problem PDDL may suffer from one or more of the following issues:
- Incorrect Object Count: The number of declared objects is inaccurate. If typed, the number of objects of specific types may be wrong.
- Syntactical Errors: The PDDL is not parseable due to violations of the {requirements} subset of PDDL syntax, use of undefined objects, or other syntactical mistakes.
- Unsolvable Problem: No plan can achieve the goal state from the given initial state due to one of the following reasons:
  - Impossible Initial/Goal State: The initial and/or goal state contain contradictory predicates.
  - Path Infeasibility: Even if both initial and goal states are individually consistent, there is no sequence of actions that can transform the initial state into the goal state.
- Semantically Incorrect: The PDDL representation is not faithful to the natural language description. This is caused by inaccuracies in the initial state, the goal state, or both. Note that while deemed incorrect, elements of the initial and/or goal states may still be partially correct but lack necessary predicates for a complete specification.

Unparseable PDDL cannot be solvable or semantically correct. Similarly, unsolvable PDDL cannot be semantically correct. In these cases, no specific feedback will be provided on later issues, but you may be able to identify/prevent them.

Provide a single paragraph reflecting on the potential causes of the failed attempt and propose corrections. Carefully consider whether modifications are necessary for the initial state, goal state, or both.
"""
    
    if "reasoning" in experiential_agent_resp:
        reasoning_str = f"""Reasoning:
{experiential_agent_resp["reasoning"]}

"""
    else:
        reasoning_str = ""

    if "objects" in experiential_agent_resp:
        objects_str = f"""Determined objects to use:
{experiential_agent_resp["objects"]}

"""
    else:
        objects_str = ""

    # User Prompt
    user_prompt = f"""Problem:
{problem_nl}

Modeler Agent's failed attempt:

{reasoning_str}{objects_str}Generated problem PDDL:
{experiential_agent_resp["problem_pddl"]}

Evaluation feedback:
{get_feedback_str(evaluation)}

Your reflection:
"""

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model)
    
    # Response
    response = {
        "prompts": [{"system_prompt" : system_prompt, "user_prompt" : user_prompt}],
        "reflection" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response