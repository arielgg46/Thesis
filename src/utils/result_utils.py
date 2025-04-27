def initialize_result_structures(agent_results, domain_results, agent, domain, dom_path, ex, eval_result, agent_output, model):
    idx = ex["id"]
    agent_dict = agent_results.setdefault(agent, {
        "name": agent,
        "parameters": {"llm_model" : model},
        "domains": {}
    })

    dom_dict_a = agent_dict["domains"].setdefault(domain, {
        "name": domain,
        "domain_pddl": open(dom_path, encoding="utf-8").read(),
        "problems": {}
    })

    dom_dict_d = domain_results.setdefault(domain, {
        "name": domain,
        "domain_pddl": open(dom_path, encoding="utf-8").read(),
        "problems": {}
    })

    # agent-based structure
    dom_dict_a["problems"][idx] = {**ex, "split": "split", "plan_gt": "", "plan_pred": "", "eval": eval_result}

    # domain-based structure
    prob_dict = dom_dict_d["problems"].setdefault(idx, {**ex, "split": "split", "plan_gt": "", "agents": {}})
    prob_dict["agents"][agent] = {
        "name": agent,
        "parameters": {"llm_model" : model},
        "eval": eval_result,
        "plan_pred": ""
    }

    return dom_dict_a, prob_dict
