from utils.client import make_fw_client
from domains.utils import get_domain_pddl, get_domain_description, get_domain_requirements

# LLM+P
def get_problem_pddl_llm_plus_p(problem_nl: str, 
    domain: str, 
    api_key: str, 
    model: str):
    
    domain_pddl = get_domain_pddl(domain)
    domain_description = get_domain_description(domain)
    requirements = get_domain_requirements(domain)

    system_prompt = f"""Domain: {domain}
{domain_description}

Domain PDDL:
{domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain.
Provide the problem PDDL (that conforms to the grammar of the {requirements} subset of PDDL) of this problem, WITH NO FURTHER EXPLANATION.
"""
    
    user_prompt = f"""Problem:
{problem_nl}

Problem PDDL:
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
        "problem_pddl" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response