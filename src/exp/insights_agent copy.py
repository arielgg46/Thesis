import json
from typing import List

from client.client import llm_query
from domains.utils import get_domain_pddl, get_domain_description
from config import INSIGHTS_LIMIT, OPERATIONS_LIMIT

def compare_fail_vs_succ(successful_trial,
                         failed_trial,
                         existing_insights,
                         api_key: str, 
                         model: str) -> dict:
                
    domain = successful_trial["task"]["domain"]
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    problem_nl = successful_trial["task"]["natural_language"]

    fail_explanation = failed_trial["eval"]["feedback"]

    instruction = f"""You are an advanced reasoning agent that can add, edit or remove rules from your existing rule set, based on forming new critiques of past tasks atempts.
You will be given two previous task trials (one successful and one unsuccessful) in which you were given the description of a planning domain, the Domain PDDL file, and the natural language description of a problem in this domain, and were requested to provide the objects to use and the Problem PDDL file:

Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Problem:
{problem_nl}
---"""
    
    reflection_str = ""
    if failed_trial["trial"] == successful_trial["trial"] - 1:
        reflection_str = f"""
Reflection on the failed trial:
{successful_trial["successful_trial"]}
---

"""
    
    atempts_info = f"""Failed atempt:
Determined objects to use:
{failed_trial["agent_resp"]["objects"]}

Generated problem PDDL:
{failed_trial["agent_resp"]["problem_pddl"]}

Evaluation feedback:
{failed_trial["eval"]}
---
{reflection_str}
Successful atempt:
Determined objects to use:
{successful_trial["agent_resp"]["objects"]}

Generated problem PDDL:
{successful_trial["agent_resp"]["problem_pddl"]}
---"""
    
    rules_info = f"""Here are the EXISTING RULES:
{existing_insights}

By examining and contrasting the failed trial to the successful trial, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules is GENERAL and HIGH LEVEL critiques of the failed trial or proposed way of Thought so they can be used to avoid similar failures when encountered with different questions in the future. Have an emphasis on critiquing how to perform better Thought and Action. Follow the below format:
<OPERATION> <RULE NUMBER>: <RULE>

The available operations are: AGREE (if the existing rule is strongly relevant for the task), REMOVE (if one existing rule is contradictory or similar/duplicated to other existing rules), EDIT (if any existing rule is not general enough or can be enhanced, rewrite and improve it), ADD (add new rules that are very different from existing rules and relevant for other tasks). Each needs to CLOSELY follow their corresponding formatting below (any existing rule not edited, not agreed, nor removed is considered copied):

AGREE <EXISTING RULE NUMBER>: <EXISTING RULE>
REMOVE <EXISTING RULE NUMBER>: <EXISTING RULE>
EDIT <EXISTING RULE NUMBER>: <NEW MODIFIED RULE>
ADD <NEW RULE NUMBER>: <NEW RULE>

Do not mention the trials in the rules because all the rules should be GENERALLY APPLICABLE. Each rule should be concise and easy to follow. Any operation can be used MULTIPLE times. Do at most {OPERATIONS_LIMIT} operations and each existing rule can only get a maximum of 1 operation.
"""
    
    if len(existing_insights) == INSIGHTS_LIMIT:
        critique_summary_suffix = """Focus on REMOVE rules first, and stop ADD rule unless the new rule is VERY insightful and different from EXISTING RULES. Below are the operations you do to the above list of EXISTING RULES:
"""
    else:
        critique_summary_suffix = """Below are the operations you do to the above list of EXISTING RULES:
"""

    # System Prompt
    system_prompt = f"""{instruction}

{atempts_info}

{rules_info}
"""
    
    # User Prompt
    user_prompt = f"""{critique_summary_suffix}"""

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model)
    
    # Response
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "operations" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response


# Tasks from same domain
def compare_successes(successes,
                    existing_insights,
                    api_key: str, 
                    model: str) -> dict:
                
    domain = successes[0]["task"]["domain"]
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)

    instruction = f"""You are an advanced reasoning agent that can add, edit or remove rules from your existing rule set, based on forming new critiques of past tasks atempts.
You will be given a successful atempt on each of {len(successes)} tasks. In each of them which you were given the description of the same planning domain, the Domain PDDL file, and the natural language description of the problem, and were requested to provide the objects to use and the Problem PDDL file:

Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}
---"""
    
    atempts_info = ""
    for i in range(len(successes)):
        succ = successes[i]
        atempts_info += f"""Problem #{i + 1}:
{succ["task"]["natural_language"]}

Determined objects to use:
{succ["agent_resp"]["objects"]}

Generated problem PDDL:
{succ["agent_resp"]["problem_pddl"]}
---

"""
    
    rules_info = f"""Here are the EXISTING RULES:
{existing_insights}

By examining the successful trials, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules are general and high level insights of the successful trials or proposed way of Thought so they can be used as helpful tips to different tasks in the future. Have an emphasis on tips that help the agent generate correct PDDL, semantically faithful to the problem description, respecting the constraints of the domain. Follow the below format:
<OPERATION> <RULE NUMBER>: <RULE>

The available operations are: AGREE (if the existing rule is strongly relevant for the task), REMOVE (if one existing rule is contradictory or similar/duplicated to other existing rules), EDIT (if any existing rule is not general enough or can be enhanced, rewrite and improve it), ADD (add new rules that are very different from existing rules and relevant for other tasks). Each needs to CLOSELY follow their corresponding formatting below (any existing rule not edited, not agreed, nor removed is considered copied):

AGREE <EXISTING RULE NUMBER>: <EXISTING RULE>
REMOVE <EXISTING RULE NUMBER>: <EXISTING RULE>
EDIT <EXISTING RULE NUMBER>: <NEW MODIFIED RULE>
ADD <NEW RULE NUMBER>: <NEW RULE>

Do not mention the trials in the rules because all the rules should be GENERALLY APPLICABLE. Each rule should be concise and easy to follow. Any operation can be used MULTIPLE times. Do at most {OPERATIONS_LIMIT} operations and each existing rule can only get a maximum of 1 operation.
"""
    
    if len(existing_insights) == INSIGHTS_LIMIT:
        critique_summary_suffix = """Focus on REMOVE rules first, and stop ADD rule unless the new rule is VERY insightful and different from EXISTING RULES. Below are the operations you do to the above list of EXISTING RULES:
"""
    else:
        critique_summary_suffix = """Below are the operations you do to the above list of EXISTING RULES:
"""

    # System Prompt
    system_prompt = f"""{instruction}

{atempts_info}

{rules_info}
"""
    
    # User Prompt
    user_prompt = f"""{critique_summary_suffix}"""

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model)
    
    # Response
    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "operations" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response


############### From ExpeL ###############

# SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials (one successful and one unsuccessful) in which you were {task_description}. You failed the trial because {fail_explanation}."""
# SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful tasks trials in which you were {task_description}."""


# FORMAT_RULES_OPERATION_TEMPLATE = """<OPERATION> <RULE NUMBER>: <RULE>

# The available operations are: AGREE (if the existing rule is strongly relevant for the task), REMOVE (if one existing rule is contradictory or similar/duplicated to other existing rules), EDIT (if any existing rule is not general enough or can be enhanced, rewrite and improve it), ADD (add new rules that are very different from existing rules and relevant for other tasks). Each needs to CLOSELY follow their corresponding formatting below (any existing rule not edited, not agreed, nor removed is considered copied):

# AGREE <EXISTING RULE NUMBER>: <EXISTING RULE>
# REMOVE <EXISTING RULE NUMBER>: <EXISTING RULE>
# EDIT <EXISTING RULE NUMBER>: <NEW MODIFIED RULE>
# ADD <NEW RULE NUMBER>: <NEW RULE>

# Do not mention the trials in the rules because all the rules should be GENERALLY APPLICABLE. Each rule should be concise and easy to follow. Any operation can be used MULTIPLE times. Do at most {lim_operations} operations and each existing rule can only get a maximum of 1 operation. """

# CRITIQUE_SUMMARY_SUFFIX = dict(full = """Focus on REMOVE rules first, and stop ADD rule unless the new rule is VERY insightful and different from EXISTING RULES. Below are the operations you do to the above list of EXISTING RULES:
# """, not_full = """Below are the operations you do to the above list of EXISTING RULES:
# """)

# human_critique_existing_rules_all_success_template = """{instruction}
# Here are the trials:
# {success_history}

# Here are the EXISTING RULES:
# {existing_rules}

# By examining the successful trials, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules are general and high level insights of the successful trials or proposed way of Thought so they can be used as helpful tips to different tasks in the future. Have an emphasis on tips that help the agent perform better Thought and Action. Follow the below format:

# """ + FORMAT_RULES_OPERATION_TEMPLATE

# human_critique_existing_rules_template = """{instruction}
# Here are the two previous trials to compare and critique:
# TRIAL TASK:
# {task}

# SUCCESSFUL TRIAL:
# {success_history}

# FAILED TRIAL:
# {fail_history}

# Here are the EXISTING RULES:
# {existing_rules}

# By examining and contrasting to the successful trial, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules is GENERAL and HIGH LEVEL critiques of the failed trial or proposed way of Thought so they can be used to avoid similar failures when encountered with different questions in the future. Have an emphasis on critiquing how to perform better Thought and Action. Follow the below format:

# """ + FORMAT_RULES_OPERATION_TEMPLATE