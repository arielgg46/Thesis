from utils.client import make_fw_client
from domains.utils import get_domain_description, get_actions_description, get_planner_output_syntax, get_fsp_example

def get_llm_plan_fsp(problem_nl: str, 
                     domain: str, 
                     api_key: str, 
                     model: str):

    domain_description = get_domain_description(domain)
    actions_description = get_actions_description(domain)
    planner_output_syntax = get_planner_output_syntax(domain)

    fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects = get_fsp_example(domain)

    system_prompt = f"""Domain: {domain}
{domain_description}

{actions_description}

Task:
You will receive a planning problem of this domain.
Provide an optimal plan, in the way of a sequence of actions, to solve the problem.
{planner_output_syntax}

Example:
Problem:
{fsp_ex_nl}

Plan:
{fsp_ex_plan}
"""
    
    user_prompt = f"""New problem: 
{problem_nl}

Plan:
"""
    client = make_fw_client(api_key)
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt,},
            {"role": "user", "content": user_prompt},
        ]
    )

    response = {
        # "system_prompt" : system_prompt,
        # "user_prompt" : user_prompt,
        "plan" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response