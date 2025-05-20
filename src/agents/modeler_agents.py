import json
from typing import List, Dict, Optional

from client.client import llm_query
from grammar.grammar import get_pddl_problem_grammar, get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing, get_typed_objects_grammar, get_not_typed_objects_grammar
from domains.utils import get_domain_pddl, get_domain_predicates, get_domain_types, get_domain_description, get_domain_requirements, get_fsp_example
from exp.rag import get_top_similar_successes
from exp.insights_extraction import load_rules

def fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning):
    return{
        "nl": fsp_ex_nl,
        "pddl": fsp_ex_pddl,
        "plan": fsp_ex_plan,
        "objects": fsp_ex_objects,
        "reasoning": fsp_ex_reasoning
    }

class ModelerAgent:
    """
    Agent for generating PDDL problem files from natural language descriptions,
    with configurable modules for reasoning, object extraction, few-shot prompting,
    insights, reflection, and grammar-constrained decoding (GCD)......etc.
    """
    def __init__(
        self,
        pddl_generation_model: str,
        use_reasoning: bool = False,
        reasoning_model: Optional[str] = None,
        use_objects_extraction: bool = False,
        objects_extraction_model: Optional[str] = None,
        use_fsp: bool = False,
        use_rag: bool= False,
        fsp_k: int = 1,
        use_insights: bool = False,
        use_reflection: bool = False,
        use_gcd: bool = False,
        use_daps: bool = False,
    ):
        self.pddl_generation_model = pddl_generation_model
        self.use_reasoning = use_reasoning
        self.reasoning_model = reasoning_model
        self.use_objects_extraction = use_objects_extraction
        self.objects_extraction_model = objects_extraction_model
        self.use_fsp = use_fsp
        self.use_rag = use_rag
        self.fsp_k = fsp_k
        self.use_insights = use_insights
        self.use_reflection = use_reflection
        self.use_gcd = use_gcd
        self.use_daps = use_daps
        self.not_typed_objects_grammar = None
        self.objects_grammar = None

        self.domain = None
        self.problem_nl = None
        self.reasoning = None
        self.objects = None
        self.insights = None
        
        if use_objects_extraction:
            self.not_typed_objects_grammar = get_not_typed_objects_grammar()

        # State
        self.fsp_examples: List[Dict] = []
        self.reflections: List[str] = []
        self.last_resp: Optional[Dict] = None

    def set_fsp_examples(self, fsp_examples):
        self.fsp_examples = fsp_examples

    def set_domain(self, domain):
        if self.domain == domain:
            return
        
        self.domain = domain
        # Load domain resources
        self.domain_description = get_domain_description(domain)
        self.domain_pddl = get_domain_pddl(domain)
        self.domain_predicates = get_domain_predicates(domain)
        self.requirements = get_domain_requirements(domain)

        self.domain_types = []
        domain_types_dict = get_domain_types(domain)
        self.domain_types_dict = domain_types_dict
        for type in domain_types_dict:
            self.domain_types.append(type)

        if len(self.domain_types) > 0:
            self.objects_grammar = get_typed_objects_grammar(self.domain_types)
        else:
            self.objects_grammar = self.not_typed_objects_grammar

        if self.use_fsp and not self.use_rag:
            fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning = get_fsp_example(domain)
            fsp_ex = fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning)
            self.set_fsp_examples([fsp_ex])

        if self.use_insights:
            self.insights = load_rules()

    def set_task(self, domain, problem_nl):
        self.set_domain(domain)
        self.problem_nl = problem_nl
        if self.use_rag:
            fsp_examples = get_top_similar_successes(self.fsp_k) # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            self.set_fsp_examples(fsp_examples)


    def get_insights_str(self):
        if len(self.insights):
            return """"""
        
        insights_str = """

This are some insights you have gathered through experience, to guide your response:
"""

        for insight in self.insights:
            insights_str += f"""- {insight}
"""
        
        return insights_str
    
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
                    "pddl": "Problem PDDL"
                }
                fsp_str += "\n"
                if j > 0:
                    fsp_str += "\n"
                fsp_str += f"{field_preffix[field]}:\n{fsp_ex[field]}"
        return fsp_str

    def get_objects_str(self, objects_resp):
        if self.domain_types == {}:
            objects_dict = json.loads(objects_resp.choices[0].message.content)
            objects = objects_dict["objects"]
        else:
            objects_dict = json.loads(objects_resp.choices[0].message.content)
            objects = []
            for type in objects_dict:
                objects.append((type, objects_dict[type]))

        return f"""
Objects to use:
{objects}
"""

    def get_reflections_str(self) -> str:
        """
        Returns the Past trials reflections part of the prompt given
        the reflections on the past trials
        """
        reflections_str = ""
        objects_str = """"""
        if "objects" in self.last_resp:
            objects_str = f"""
Used objects:
{self.last_resp["objects"]}
"""

        if len(self.reflections) > 0:
            reflections_str = f"""
You have tried the problem before, unsuccesfully. This was your answer:
{objects_str}
Generated Problem PDDL:
{self.last_resp["problem_pddl"]}

Reflection on the previous trial:
{self.reflections[-1]}

Try again, taking into account the previous trial.

New trial:
"""
        return reflections_str

    def get_problem_objects(self):
        if self.use_reasoning:
            if self.use_fsp:
                fsp_str = self.get_fsp_str(fields = ["nl", "reasoning", "objects"])
            else:
                fsp_str = """"""
            reasoning_str = f"""
Reasoning:
{self.reasoning}
"""
        else:
            if self.use_fsp:
                fsp_str = self.get_fsp_str(fields = ["nl", "objects"])
            else:
                fsp_str = """"""
            reasoning_str = """"""
        # reflections_str = get_reflections_str(last_resp =  reflections = reflections)

        if len(self.domain_types) > 0:
            task_str = "Provide a list of all the objects in the PDDL problem instance, separated by type."
        else:
            task_str = "Provide a list of all the objects in the PDDL problem instance."

        system_prompt = f"""Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{self.domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain.
{task_str}{fsp_str}"""
        
        user_prompt = f"""New problem:
{self.problem_nl}
{reasoning_str}
Objects to use:
"""
    # {reflections_str}

        chat_completion = llm_query(system_prompt, user_prompt, self.objects_extraction_model, self.objects_grammar)

        return chat_completion

    def get_problem_reasoning(self) -> str:
        if self.use_fsp:
            fsp_str = self.get_fsp_str(fields = ["nl", "reasoning"])
        else:
            fsp_str = """"""

        if self.use_reflection:
            reflections_str = self.get_reflections_str()
        else:
            reflections_str = """"""

        if self.use_insights:
            insights_str = self.get_insights_str()
        else:
            insights_str = """"""

        system_prompt = f"""Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{self.domain_pddl}

Task:
You are an advanced planning modeling reasoning agent. When given the planning domain and a natural language description of a problem in this domain, you will *reason step by step* to resolve any ambiguities or missing details, to help to improve the semantic correctness of a posterior problem PDDL generation by another model.
Write your reasoning as exactly 3 paragraphs of no more than 100 words each. In them you should cover, in order:

1. **Objects**: list every object by name.  
2. **Initial state**: describe the initial state, and any assumptions you make to fill in missing info.  
3. **Goal state**: describe the goal state, and any assumptions you make to fill in missing info.

Fully specify the subgoals and initial state as detailed as you can. Don't reason about the planning itself, just the PDDL. Don't extend beyond 3 short paragraphs.{fsp_str}
{insights_str}"""
        
        user_prompt = f"""New problem:
{self.problem_nl}
{reflections_str}
Reasoning:
"""

        chat_completion = llm_query(system_prompt, user_prompt, self.reasoning_model)

        return chat_completion


    def solve_task(self) -> dict:
        response = {}
        prompt_tokens = []
        completion_tokens = []
        total_tokens = []
    
        # 1) Reasoning
        if self.use_reasoning:
            reasoning_resp = self.get_problem_reasoning()
            reasoning = reasoning_resp.choices[0].message.content.strip()
            reasoning_str = f"""
Reasoning:
{reasoning}
"""
            response["reasoning"] = reasoning
            prompt_tokens.append(reasoning_resp.usage.prompt_tokens), 
            completion_tokens.append(reasoning_resp.usage.completion_tokens)
            total_tokens.append(reasoning_resp.usage.total_tokens)
        else:
            reasoning_str = """"""
    
        # 2) Objects
        if self.use_objects_extraction:
            objects_resp = self.get_problem_objects()
            objects_str = self.get_objects_str(objects_resp)
            
            objects_dict = json.loads(objects_resp.choices[0].message.content)

            if len(self.domain_types) == 0:
                objects = objects_dict["objects"]
            else:
                objects = []
                for type in objects_dict:
                    objects.append((type, objects_dict[type]))

            response["objects"] = objects
            prompt_tokens.append(objects_resp.usage.prompt_tokens), 
            completion_tokens.append(objects_resp.usage.completion_tokens)
            total_tokens.append(objects_resp.usage.total_tokens)
        else:
            objects_str = """"""

        # 3) Few-shot Prompting
        if self.use_fsp:
            fields = ["nl"]
            if self.use_reasoning:
                fields.append("reasoning")
            if self.use_objects_extraction:
                fields.append("objects")
            fields.append("pddl")

            fsp_str = self.get_fsp_str(fields = fields)
        else:
            fsp_str = """"""
        
        # 4) Previous trial and Reflection
        if self.use_reflection:
            reflections_str = self.get_reflections_str()
        else:
            reflections_str = """"""

        # 5) Insights
        if self.use_insights:
            insights_str = self.get_insights_str()
        else:
            insights_str = """"""

        # 6) GCD (+DAPS)
        if self.use_gcd and not self.use_daps:
            pddl_problem_grammar = get_pddl_problem_grammar(self.domain, self.domain + "_problem")
        elif self.use_objects_extraction and self.use_daps:
            if len(self.domain_types) == 0:
                pddl_problem_grammar = get_pddl_problem_grammar_daps_no_typing(self.domain, self.domain + "_problem", self.domain_predicates, objects)
            else:
                pddl_problem_grammar = get_pddl_problem_grammar_daps_typing(self.domain, self.domain + "_problem", self.domain_predicates, objects, self.domain_types_dict)
        else:
            pddl_problem_grammar = None

        # 7) PDDL Generation
        # System Prompt
        system_prompt = f"""Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{self.domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain. 
Provide the problem PDDL (that conforms to the grammar of the {self.requirements} subset of PDDL) of this problem.{fsp_str}
{insights_str}"""
        
        # User Prompt
        user_prompt = f"""New problem:
{self.problem_nl}
{reflections_str}{reasoning_str}{objects_str}
Problem PDDL:
"""

        # LLM call
        pddl_generation_resp = llm_query(system_prompt, user_prompt, self.pddl_generation_model, pddl_problem_grammar)
        
        # Response
        problem_pddl = pddl_generation_resp.choices[0].message.content
        response["problem_pddl"] = problem_pddl
        prompt_tokens.append(pddl_generation_resp.usage.prompt_tokens), 
        completion_tokens.append(pddl_generation_resp.usage.completion_tokens)
        total_tokens.append(pddl_generation_resp.usage.total_tokens)

        response["prompt_tokens"] = prompt_tokens
        response["completion_tokens"] = completion_tokens
        response["total_tokens"] = total_tokens
        return response
    
def get_modeler_agent(variant, 
                      pddl_generation_model = "accounts/fireworks/models/deepseek-v3", 
                      reasoning_model = "accounts/fireworks/models/deepseek-v3", 
                      objects_extraction_model = "accounts/fireworks/models/deepseek-v3"):
    if variant == "llm_plus_p":
        return ModelerAgent(pddl_generation_model = pddl_generation_model)
    if variant == "llm_plus_p_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_fsp = True)
    if variant == "gcd":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_gcd = True)
    if variant == "daps_gcd":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_gcd = True, use_daps = True, use_objects_extraction = True, objects_extraction_model = objects_extraction_model)
    if variant == "daps_gcd_r":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_gcd = True, use_daps = True, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_reasoning = True, reasoning_model = reasoning_model)
    if variant == "daps_gcd_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_gcd = True, use_daps = True, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_fsp = True)
    if variant == "daps_gcd_r_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_gcd = True, use_daps = True, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_reasoning = True, reasoning_model = reasoning_model, use_fsp = True)
