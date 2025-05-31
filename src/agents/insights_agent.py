import json
from typing import List
from pprint import pprint

from client.client import llm_query
from domains.utils import get_domain_pddl, get_domain_description
from config import INSIGHTS_LIMIT, OPERATIONS_LIMIT

def get_insights_str(domain, existing_insights):
    DOMAIN_KNOWLEDGE = existing_insights["agent"]["domain"][domain]["world_knowledge"]
    DOMAIN_RULES = existing_insights["agent"]["domain"][domain]["rules"]
    GENERAL = existing_insights["agent"]["general"]["rules"]

    insights_str = f"""This are the EXISTING INSIGHTS, grouped into three types:
- DOMAIN_KNOWLEDGE (insights related to world knowledge of the given planning domain):"""
    for i in range(len(DOMAIN_KNOWLEDGE)):
        insights_str += f"""
    {i+1}. {DOMAIN_KNOWLEDGE[i][0]}"""

    insights_str += """
- DOMAIN_RULES (domain-specific modeling rules, tips, or best practices):"""
    for i in range(len(DOMAIN_RULES)):
        insights_str += f"""
    {i+1}. {DOMAIN_RULES[i][0]}"""

    insights_str += """
- GENERAL (general modeling principles applicable across domains):"""
    for i in range(len(GENERAL)):
        insights_str += f"""
    {i+1}. {GENERAL[i][0]}"""
    
    return insights_str

def get_feedback_str(eval):
    feedback_str = ""
    for fb in eval["feedback"]:
        if feedback_str != "":
            feedback_str += "\n"
        feedback_str += f"- {fb}"
    return feedback_str

# Compare a failed attempt and a successful attempt of the same task
def compare_fail_vs_succ(successful_trial,
                         failed_trial,
                         existing_insights,
                         model: str) -> dict:
                
    domain = successful_trial["task"]["domain"]
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)
    problem_nl = successful_trial["task"]["natural_language"]

    insights_str = get_insights_str(domain, existing_insights)

    instruction = f"""You are an advanced Planning Modeler AI Agent that can revise a structured set of insights by adding, editing, removing, or agreeing with existing insights, based on two attempts (one successful and one unsuccessful) of the same task. In each attempt, the modeler agent received the domain description, the Domain PDDL file, and a natural language description of the problem, and produced a Problem PDDL file as output.

Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}    

{insights_str}

Your task is to update these insight lists based on patterns, lessons or recurring mistakes observed by contrasting the failed trial to the successful trial. Each operation must be applied to the list corresponding to the selected insight type.

The available operations are:
* AGREE: affirm an existing insight that is still relevant and valuable
* REMOVE: discard an insight that is incorrect, redundant, too narrow, or superseded
* EDIT: rewrite an existing insight to improve generality, clarity, or usefulness
* ADD: introduce a new insight that is not already represented in the list

You can apply up to {OPERATIONS_LIMIT} operations **per insight type**. You may perform each operation multiple times, but no existing insight may receive more than one operation. Any insight that is not explicitly marked with AGREE, REMOVE, or EDIT is assumed to be copied unchanged. Do not reference specific trials in the content of the insights — all insights must be general, reusable, and concise. Focus on insights that help the agent produce PDDL that is semantically faithful to the problem description and respects the domain constraints.
You must write each operation IN A SINGLE LINE WITHOUT ANY PREFFIX OR SUFFIX, IN ONE OF THE FOLLOWING THE EXACT FORMATS:
<INSIGHT TYPE> AGREE <EXISTING INSIGHT NUMBER>: <EXISTING INSIGHT>
<INSIGHT TYPE> REMOVE <EXISTING INSIGHT NUMBER>: <EXISTING INSIGHT>
<INSIGHT TYPE> EDIT <EXISTING INSIGHT NUMBER>: <NEW MODIFIED INSIGHT>
<INSIGHT TYPE> ADD <NEW INSIGHT NUMBER>: <NEW INSIGHT>
"""
    
    reflection_str = ""
    if failed_trial["trial"] == successful_trial["trial"] - 1:
        reflection_str = f"""
Reflection on the failed trial:
{successful_trial["reflection_on_previous_trial"]}
"""
    
    # Failed attempt
    failed_attempt_str = f"""Failed attempt:"""
    
    # reasoning
    if "reasoning" in failed_trial["agent_resp"]:
        failed_attempt_str += f"""

Reasoning:
{failed_trial["agent_resp"]["reasoning"]}"""

    # objects
    if "objects" in failed_trial["agent_resp"]:
        failed_attempt_str += f"""

Determined objects to use:
{failed_trial["agent_resp"]["objects"]}"""
    
    # pddl and feedback
    failed_attempt_str += f"""

Generated problem PDDL:
{failed_trial["agent_resp"]["problem_pddl"]}

Evaluation feedback:
{get_feedback_str(failed_trial["eval"])}"""

    # Successful attempt
    successful_attempt_str = f"""Successful attempt:"""
    
    # reasoning
    if "reasoning" in successful_trial["agent_resp"]:
        successful_attempt_str += f"""

Reasoning:
{successful_trial["agent_resp"]["reasoning"]}"""

    # objects
    if "objects" in successful_trial["agent_resp"]:
        successful_attempt_str += f"""

Determined objects to use:
{successful_trial["agent_resp"]["objects"]}"""
    
    # pddl
    successful_attempt_str += f"""

Generated problem PDDL:
{failed_trial["agent_resp"]["problem_pddl"]}"""
    
    # Attempts info
    attempts_info = f"""Problem:
{problem_nl}

{failed_attempt_str}
{reflection_str}
{successful_attempt_str}"""
    
    if len(existing_insights) >= INSIGHTS_LIMIT:
        critique_summary_suffix = """Focus on REMOVE operations first, and stop ADD operations unless the new insight is VERY important and different from EXISTING INSIGHTS. Below are the operations you do to the above list of EXISTING INSIGHTS:
"""
    else:
        critique_summary_suffix = """Below are the operations you do to the above list of EXISTING INSIGHTS:
"""

    # System Prompt
    system_prompt = f"""{instruction}

{attempts_info}
"""
    
    # User Prompt
    user_prompt = f"""{critique_summary_suffix}"""

    # print("###########################################################################")
    # print("######################### SYSTEM #########################")
    # print(system_prompt)
    # print()
    # print()
    # print("######################### USER #########################")
    # print(user_prompt)
    # print("###########################################################################")
    # print()
    # print()

    return

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


# Compare successful attempts of different tasks of the same domain
def compare_successes(successes,
                    existing_insights,
                    model: str) -> dict:
                
    domain = successes[0]["task"]["domain"]
    domain_description = get_domain_description(domain)
    domain_pddl = get_domain_pddl(domain)

    insights_str = get_insights_str(domain, existing_insights)

    # Instruction
    instruction = f"""You are an advanced Planning Modeler AI Agent that can revise a structured set of insights by adding, editing, removing, or agreeing with existing insights, based on successful task attempts. In each task, the same planning domain was used, and the modeler agent received the domain description, the Domain PDDL file, and a natural language description of the problem, and produced a Problem PDDL file as output.

Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

{insights_str}

Your task is to update these insight lists based on patterns or lessons observed from the successful trials. Each operation must be applied to the list corresponding to the selected insight type.

The available operations are:
* AGREE: affirm an existing insight that is still relevant and valuable
* REMOVE: discard an insight that is incorrect, redundant, too narrow, or superseded
* EDIT: rewrite an existing insight to improve generality, clarity, or usefulness
* ADD: introduce a new insight that is not already represented in the list


You can apply up to {OPERATIONS_LIMIT} operations **per insight type**. You may perform each operation multiple times, but no existing insight may receive more than one operation. Any insight that is not explicitly marked with AGREE, REMOVE, or EDIT is assumed to be copied unchanged. Do not reference specific trials in the content of the insights — all insights must be general, reusable, and concise. Focus on insights that help the agent produce PDDL that is semantically faithful to the problem description and respects the domain constraints.
You must write each operation IN A SINGLE LINE WITHOUT ANY PREFFIX OR SUFFIX, IN ONE OF THE FOLLOWING THE EXACT FORMATS:
<INSIGHT TYPE> AGREE <EXISTING INSIGHT NUMBER>: <EXISTING INSIGHT>
<INSIGHT TYPE> REMOVE <EXISTING INSIGHT NUMBER>: <EXISTING INSIGHT>
<INSIGHT TYPE> EDIT <EXISTING INSIGHT NUMBER>: <NEW MODIFIED INSIGHT>
<INSIGHT TYPE> ADD <NEW INSIGHT NUMBER>: <NEW INSIGHT>
"""
    
    # Successful attempts info
    attempts_info = ""
    for i in range(len(successes)):
        succ = successes[i]
        attempts_info += f"""Problem #{i + 1}:
{succ["task"]["natural_language"]}"""

        if "reasoning" in succ["agent_resp"]:
            attempts_info += f"""

Reasoning:
{succ["agent_resp"]["reasoning"]}"""

        if "objects" in succ["agent_resp"]:
            attempts_info += f"""

Determined objects to use:
{succ["agent_resp"]["objects"]}"""

        attempts_info += f"""

Generated problem PDDL:
{succ["agent_resp"]["problem_pddl"]}
---

"""
    
    # End
    if len(existing_insights) >= INSIGHTS_LIMIT:
        critique_summary_suffix = """Focus on REMOVE operations first, and stop ADD operations unless the new insight is VERY important and different from EXISTING INSIGHTS. Below are the operations you do to the above list of EXISTING INSIGHTS:
"""
    else:
        critique_summary_suffix = """Prioritize adding new interesting insights, about useful patterns observed in good solutions. Below are the operations you do to the above list of EXISTING INSIGHTS:
"""

    # System Prompt
    system_prompt = f"""{instruction}

{attempts_info}
"""
    
    # User Prompt
    user_prompt = f"""{critique_summary_suffix}"""

    # LLM call
    chat_completion = llm_query(system_prompt, user_prompt, model)

    # print("-----------------------------------------------------------")
    # print("-----------------------------------------------------------")
    # print("-----------------------------------------------------------")
    # print("##################### SYSTEM PROMPT #####################")
    # pprint(system_prompt)
    # print()
    # print()
    # print("##################### USER PROMPT #####################")
    # pprint(user_prompt)
    # print("-----------------------------------------------------------")
    # print("-----------------------------------------------------------")
    # print("-----------------------------------------------------------")
    # print()
    # print()
    
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