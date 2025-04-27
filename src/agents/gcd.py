from utils.client import make_fw_client
from grammar.grammar import get_pddl_problem_grammar
from domains.utils import get_domain_pddl, get_domain_description, get_domain_requirements

# LLM+P with Grammar Constrained Decoding
def get_problem_pddl_gcd(problem_nl: str, 
                     domain: str, 
                     api_key: str, 
                     model: str):
    
    domain_pddl = get_domain_pddl(domain)
    pddl_problem_grammar = get_pddl_problem_grammar(domain, domain + "_problem")
    domain_description = get_domain_description(domain)
    requirements = get_domain_requirements(domain)

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
        "problem_pddl" : chat_completion.choices[0].message.content, 
        "prompt_tokens" : [chat_completion.usage.prompt_tokens], 
        "completion_tokens" : [chat_completion.usage.completion_tokens], 
        "total_tokens" : [chat_completion.usage.total_tokens]
    }
    return response