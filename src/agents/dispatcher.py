from agents.llm_planner import get_llm_plan
from agents.llm_planner_fsp import get_llm_plan_fsp
from agents.llm_plus_p import get_problem_pddl_llm_plus_p
from agents.llm_plus_p_fsp import get_problem_pddl_llm_plus_p_fsp
from agents.gcd import get_problem_pddl_gcd
from agents.daps_gcd import get_problem_pddl_daps_gcd
from agents.reasoning import get_problem_pddl_daps_gcd_reasoning
from agents.daps_gcd_fsp import get_problem_pddl_daps_gcd_fsp 

def generate_with_agent(nl: str, domain: str, api_key: str, agent: str, model: str = "accounts/fireworks/models/deepseek-v3"): 
    """Dispatch to the correct generator based on agent name."""
    if agent == "llm_planner":
        return get_llm_plan(nl, domain, api_key, model)
    if agent == "llm_planner_fsp":
        return get_llm_plan_fsp(nl, domain, api_key, model)
    if agent == "llm_plus_p":
        return get_problem_pddl_llm_plus_p(nl, domain, api_key, model)
    if agent == "llm_plus_p_fsp":
        return get_problem_pddl_llm_plus_p_fsp(nl, domain, api_key, model)
    if agent == "gcd":
        return get_problem_pddl_gcd(nl, domain, api_key, model)
    if agent == "daps_gcd":
        return get_problem_pddl_daps_gcd(nl, domain, api_key, model)
    if agent == "daps_gcd_r":
        return get_problem_pddl_daps_gcd_reasoning(nl, domain, api_key, model, reasoning_model="accounts/fireworks/models/deepseek-v3")
    if agent == "daps_gcd_fsp":
        return get_problem_pddl_daps_gcd_fsp(nl, domain, api_key, model)
    # ...
    raise ValueError(f"Unknown agent {agent}")

#accounts/fireworks/models/qwq-32b
#accounts/fireworks/models/llama-v3p1-8b-instruct