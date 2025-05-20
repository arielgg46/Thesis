import json
from typing import List, Dict, Optional
from client.client import llm_query
from domains.utils import get_domain_pddl, get_actions_description, get_planner_output_syntax, get_domain_description, get_domain_requirements, get_fsp_example

def fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning):
    return{
        "nl": fsp_ex_nl,
        "pddl": fsp_ex_pddl,
        "plan": fsp_ex_plan,
        "objects": fsp_ex_objects,
        "reasoning": fsp_ex_reasoning
    }

class PlannerAgent:
    """
    Agent for generating PDDL plans from natural language descriptions,
    with configurable module for few-shot prompting.
    """
    def __init__(
        self,
        planning_model: str,
        use_fsp: bool = False
    ):
        self.planning_model = planning_model
        self.use_fsp = use_fsp

        self.domain = None
        self.problem_nl = None
        
        # State
        self.fsp_examples: List[Dict] = []

    def set_fsp_examples(self, fsp_examples):
        self.fsp_examples = fsp_examples

    def set_domain(self, domain):
        if self.domain == domain:
            return
        
        self.domain = domain
        # Load domain resources
        self.domain_description = get_domain_description(domain)
        self.domain_pddl = get_domain_pddl(domain)
        self.requirements = get_domain_requirements(domain)
        self.actions_description = get_actions_description(domain)
        self.planner_output_syntax = get_planner_output_syntax(domain)

        if self.use_fsp:
            fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning = get_fsp_example(domain)
            fsp_ex = fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning)
            self.set_fsp_examples([fsp_ex])

    def set_task(self, domain, problem_nl):
        self.set_domain(domain)
        self.problem_nl = problem_nl
    
    def get_fsp_str(self, fields: List[str]) -> str:
        """
        Returns the Few-Shot Prompting part of the prompt given
        few-shot examples, and the fields of the examples to include
        """
        fsp_str = ""
        for i in range(len(self.fsp_examples)):
            fsp_ex = self.fsp_examples[i]
            if i > 0:
                fsp_str += "\n"
            else:
                fsp_str += "\n\n"
            fsp_str += f"Example #{i+1}:"
            for j in range(len(fields)):
                field = fields[j]
                field_preffix = {
                    "nl": "Problem",
                    "reasoning": "Reasoning",
                    "objects": "Objects to use",
                    "pddl": "Problem PDDL",
                    "plan": "Plan"
                }
                fsp_str += "\n"
                if j > 0:
                    fsp_str += "\n"
                fsp_str += f"{field_preffix[field]}:\n{fsp_ex[field]}"
        return fsp_str

    def solve_task(self) -> dict:
        response = {}
        prompt_tokens = []
        completion_tokens = []
        total_tokens = []

        # 1) Few-shot Prompting
        if self.use_fsp:
            fields = ["nl", "plan"]
            fsp_str = self.get_fsp_str(fields = fields)
        else:
            fsp_str = """"""

        # 2) Plan PDDL Generation
        system_prompt = f"""Domain: {self.domain}
{self.domain_description}

{self.actions_description}

Task:
You will receive a planning problem of this domain.
Provide an optimal plan, in the way of a sequence of actions, to solve the problem.
{self.planner_output_syntax}{fsp_str}
"""
    
        user_prompt = f"""New problem: 
{self.problem_nl}

Plan:
"""

        # LLM call
        plan_generation_resp = llm_query(system_prompt, user_prompt, self.planning_model)
        
        # Response
        plan = plan_generation_resp.choices[0].message.content
        response["plan"] = plan
        prompt_tokens.append(plan_generation_resp.usage.prompt_tokens), 
        completion_tokens.append(plan_generation_resp.usage.completion_tokens)
        total_tokens.append(plan_generation_resp.usage.total_tokens)

        response["prompt_tokens"] = prompt_tokens
        response["completion_tokens"] = completion_tokens
        response["total_tokens"] = total_tokens
        return response
    
def get_planner_agent(variant, 
                      plan_generation_model = "accounts/fireworks/models/deepseek-v3"):
    if variant == "llm_planner":
        return PlannerAgent(planning_model = plan_generation_model)
    if variant == "llm_planner_fsp":
        return PlannerAgent(planning_model = plan_generation_model, use_fsp = True)