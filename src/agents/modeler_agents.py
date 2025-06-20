import json
from typing import List, Dict, Optional
from pprint import pprint

from client.client import llm_query
from grammar.grammar import get_pddl_problem_grammar, get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing, get_typed_objects_grammar, get_not_typed_objects_grammar
from domains.utils import get_domain_pddl, get_domain_pddl_wo_actions, get_domain_predicates, get_domain_types, get_domain_description, get_domain_requirements, get_fsp_example
from exp.insights_extraction import load_insights
from rag.retriever import Retriever
from agents.reflection_agent import get_feedback_str

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
        use_comments: bool = False
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
        self.use_comments = use_comments
        self.comments_str = ""
        if self.use_comments:
            self.comments_str = "Before each predicate in the :init and :goal sections you can use at most 1 short one-line comment to describe the start of a relevant section of definitions."

        self.domain = None
        self.problem_nl = None
        self.reasoning = None
        self.objects = None
        if self.use_insights:
            self.insights = load_insights()
        
        if use_objects_extraction:
            self.not_typed_objects_grammar = get_not_typed_objects_grammar()

        # State
        if self.use_fsp:
            self.fsp_examples: List[Dict] = []
        self.reflections: List[str] = []
        self.last_resp: Optional[Dict] = {}

        self.retriever = Retriever()

    def trial_to_fsp_ex(self, trial):
        fsp_ex = {
            "nl": trial["task"]["natural_language"],
            "pddl": trial["agent_resp"]["problem_pddl"]
        }

        if "reasoning" in trial["agent_resp"]:
            fsp_ex["reasoning"] = trial["agent_resp"]["reasoning"]

        if "objects" in trial["agent_resp"]:
            fsp_ex["objects"] = trial["agent_resp"]["objects"]

        return fsp_ex


    def set_fsp_examples(self, fsp_examples):
        self.fsp_examples = fsp_examples

    def set_domain(self, domain):
        if self.domain == domain:
            return
        
        self.domain = domain
        # Load domain resources
        self.domain_description = get_domain_description(domain)
        self.domain_pddl = get_domain_pddl(domain)
        if domain == "floor-tile":
            self.domain_pddl_wo_actions = get_domain_pddl_wo_actions(domain)
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

        if self.use_fsp and (not self.use_rag or self.domain == "floor-tile"):
            fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning = get_fsp_example(domain)
            fsp_ex = fsp_to_dict(fsp_ex_nl, fsp_ex_pddl, fsp_ex_plan, fsp_ex_objects, fsp_ex_reasoning)
            self.set_fsp_examples([fsp_ex])

    def set_task(self, id, domain, problem_nl):
        self.problem_id = id
        self.set_domain(domain)
        self.problem_nl = problem_nl
        if self.use_rag and self.domain != "floor-tile":
            similar_succ = self.retriever.get_top_similar_successes(self.problem_id, self.fsp_k)
            fsp_examples = [self.trial_to_fsp_ex(trial) for trial in similar_succ]
            self.set_fsp_examples(fsp_examples)
        
        self.prompts = []


    def get_insights_str(self):
        # DOMAIN_KNOWLEDGE = self.insights["agent"]["domain"][self.domain]["world_knowledge"]
        # DOMAIN_RULES = self.insights["agent"]["domain"][self.domain]["rules"]
        # GENERAL = self.insights["agent"]["general"]["rules"]

        DOMAIN_KNOWLEDGE = self.insights["human"]["domain"][self.domain]["world_knowledge"]
        DOMAIN_RULES = self.insights["human"]["domain"][self.domain]["rules"]
        GENERAL = self.insights["human"]["general"]["rules"]

        if len(DOMAIN_KNOWLEDGE) == 0 and len(DOMAIN_RULES) == 0 and len(GENERAL) == 0:
            return ""
        
        insights_str = f"""

This are some insights you have gathered through experience, to guide your response:"""
        
        if len(DOMAIN_KNOWLEDGE) > 0:
            insights_str += f"""
- DOMAIN_KNOWLEDGE (insights related to world knowledge of the given planning domain):"""
            for i in range(len(DOMAIN_KNOWLEDGE)):
                insights_str += f"""
    {i+1}. {DOMAIN_KNOWLEDGE[i][0]}"""

        if len(DOMAIN_RULES) > 0:
            insights_str += """
- DOMAIN_RULES (domain-specific modeling rules, tips, or best practices):"""
            for i in range(len(DOMAIN_RULES)):
                insights_str += f"""
    {i+1}. {DOMAIN_RULES[i][0]}"""

        if len(GENERAL) > 0:
            insights_str += """
- GENERAL (general modeling principles applicable across domains):"""
            for i in range(len(GENERAL)):
                insights_str += f"""
    {i+1}. {GENERAL[i][0]}"""
        
        insights_str += """

Make sure to FOLLOW CLOSELY this insights, specially the DOMAIN_RULES"""
        return insights_str
    
    def get_fsp_str(self, fields: List[str]) -> str:
        """
        Returns the Few-Shot Prompting part of the prompt given
        few-shot examples, and the fields of the examples to include
        """

        field_preffix = {
            "nl": "Problem",
            "reasoning": "Reasoning",
            "objects": "Objects to use",
            "pddl": "Problem PDDL"
        }

        fsp_str = ""
        for i in range(len(self.fsp_examples)):
            fsp_ex = self.fsp_examples[i]
            if i > 0:
                fsp_str += "\n"
            else:
                fsp_str += "\n\n"
            fsp_str += f"Example #{i+1}:"
            F = True

            for j in range(len(fields)):
                field = fields[j]
                if not (field in fsp_ex):
                    continue
                fsp_str += "\n"
                if F:
                    F = False
                else:
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
        if len(self.reflections) == 0:
            return ""
        
        reflections_str = ""

        reasoning_str = """"""
        if "reasoning" in self.last_resp:
            reasoning_str = f"""

Reasoning:
{self.last_resp["reasoning"]}
"""
        
        objects_str = """"""
        if "objects" in self.last_resp:
            objects_str = f"""

Used objects:
{self.last_resp["objects"]}
"""
        
        reflections_str = f"""
You have tried the problem before, unsuccesfully. This was your answer:{reasoning_str}{objects_str}

Generated Problem PDDL:
{self.last_resp["problem_pddl"]}

Evaluation feedback:
{get_feedback_str(self.last_resp["eval"])}

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

        if self.use_reflection and not self.use_reasoning:
            reflections_str = self.get_reflections_str()
        else:
            reflections_str = """"""

        if len(self.domain_types) > 0:
            task_str = "Provide a JSON of all the objects in the PDDL problem instance, separated by type."
        else:
            task_str = "Provide a JSON of all the objects in the PDDL problem instance."

        if self.domain in ["floor-tile"]:
            domain_pddl_str = self.domain_pddl_wo_actions
        else:
            domain_pddl_str = self.domain_pddl

        system_prompt = f"""You are an advanced Planning Modeler AI Agent specialized en objects extraction. You are given the description and PDDL code of a planning domain and the natural language descriptions of problems in this domain, and for each you provide a JSON of all the objects in the PDDL problem instance.
        
Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{domain_pddl_str}

Task:
You will be given natural language descriptions of planning problems in this domain.
{task_str}{fsp_str}"""
        
        user_prompt = f"""New problem:
{self.problem_nl}
{reflections_str}
{reasoning_str}
Objects to use:
"""

        chat_completion = llm_query(system_prompt, user_prompt, self.objects_extraction_model, self.objects_grammar)
        self.prompts.append({"system_prompt": system_prompt, "user_prompt": user_prompt})

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

        system_prompt = f"""You are an advanced Planning Modeler AI Agent specialized in reasoning. You are given the description and PDDL code of a planning domain and the natural language descriptions of problems in this domain, and for each you provide a structured reasoning about the problem for its translation to PDDL.
        
Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{self.domain_pddl}

Task:
You will be given natural language descriptions of planning problems in this domain.
*Reason step by step* to resolve any ambiguities or missing details, to help to improve the semantic correctness of a posterior problem PDDL generation by another Planning Modeler Agent.
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
        self.prompts.append({"system_prompt": system_prompt, "user_prompt": user_prompt})

        return chat_completion


    def solve_task(self) -> dict:
        response = {}
        prompt_tokens = []
        completion_tokens = []
        total_tokens = []
        prompts = []
    
        # 1) Reasoning
        if self.use_reasoning:
            reasoning_resp = self.get_problem_reasoning()
            reasoning = reasoning_resp.choices[0].message.content.strip()
            self.reasoning = reasoning
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
            if len(self.reflections) > 0:
                response["reflection"] = self.reflections[-1]
        else:
            reflections_str = """"""

        # 5) Insights
        if self.use_insights:
            insights_str = self.get_insights_str()
        else:
            insights_str = """"""

        # 6) GCD (+DAPS)
        if self.use_gcd and not self.use_daps:
            pddl_problem_grammar = get_pddl_problem_grammar(self.domain, self.domain + "_problem", use_comments = self.use_comments)
        elif self.use_objects_extraction and self.use_daps:
            if len(self.domain_types) == 0:
                pddl_problem_grammar = get_pddl_problem_grammar_daps_no_typing(self.domain, self.domain + "_problem", self.domain_predicates, objects, use_comments = self.use_comments)
            else:
                pddl_problem_grammar = get_pddl_problem_grammar_daps_typing(self.domain, self.domain + "_problem", self.domain_predicates, objects, self.domain_types_dict, use_comments = self.use_comments)
        else:
            pddl_problem_grammar = None

        if self.domain in ["floor-tile"]:
            domain_pddl_str = self.domain_pddl_wo_actions
        else:
            domain_pddl_str = self.domain_pddl

        # 7) PDDL Generation
        # System Prompt
        system_prompt = f"""You are an advanced Planning Modeler AI Agent specialized in PDDL generation. You are given the description and PDDL code of a planning domain and the natural language descriptions of problems in this domain, and for each you provide the PDDL code of the problem.

Domain: {self.domain}
{self.domain_description}

Domain PDDL:
{domain_pddl_str}

Task:
You will be given natural language descriptions of planning problems in this domain. 
Provide the PDDL code (that conforms to the grammar of the {self.requirements} subset of PDDL) of this problem, without further explanation.{self.comments_str}{fsp_str}
{insights_str}"""
        # Can add "make sure the problem PDDL is parseable (sintactically valid), solvable (it is possible to find a plan from the initial to the goal state, and they don't have contradictory predicates), and correct (semantically faithful to the problem description)."

        # User Prompt
        user_prompt = f"""New problem:
{self.problem_nl}
{reflections_str}{reasoning_str}{objects_str}
Problem PDDL:
"""

        # LLM call
        pddl_generation_resp = llm_query(system_prompt, user_prompt, self.pddl_generation_model, pddl_problem_grammar)
        self.prompts.append({"system_prompt": system_prompt, "user_prompt": user_prompt})

        # Response
        problem_pddl = pddl_generation_resp.choices[0].message.content
        response["problem_pddl"] = problem_pddl
        prompt_tokens.append(pddl_generation_resp.usage.prompt_tokens), 
        completion_tokens.append(pddl_generation_resp.usage.completion_tokens)
        total_tokens.append(pddl_generation_resp.usage.total_tokens)

        # print("------------------------------------------------------------------")
        # print("------------------------------------------------------------------")
        # print("------------------------------------------------------------------")
        # print("###################### SYSTEM PROMPT ######################")
        # print(system_prompt)
        # print()
        # print()
        # print("###################### USER PROMPT ######################")
        # print(user_prompt)
        # print()
        # print()
        # print("###################### RESPONSE ######################")
        # print(response)
        # print("------------------------------------------------------------------")
        # print("------------------------------------------------------------------")
        # print("------------------------------------------------------------------")
        # print()
        # print()

        response["prompt_tokens"] = prompt_tokens
        response["completion_tokens"] = completion_tokens
        response["total_tokens"] = total_tokens
        response["prompts"] = self.prompts
        return response
    
def get_modeler_agent(variant, 
                      pddl_generation_model, 
                      reasoning_model, 
                      objects_extraction_model):
    if variant == "llm_plus_p":
        return ModelerAgent(pddl_generation_model = pddl_generation_model)
    if variant == "llm_plus_p_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_fsp = True, fsp_k = 1)
    
    if variant == "r":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model)
    if variant == "r_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_fsp = True, fsp_k = 1)
    
    if variant == "r_o":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model)
    if variant == "r_o_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_fsp = True, fsp_k = 1)
    
    if variant == "r_o_gcd":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_comments = True)
    if variant == "r_o_gcd_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_comments = True, use_fsp = True, fsp_k = 1)
    
    if variant == "r_o_daps_gcd":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True)
    if variant == "r_o_daps_gcd_fsp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True, use_fsp = True, fsp_k = 1)
    
    # Experientials
    if variant == "exp":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True, use_fsp = True, fsp_k = 1,  use_reflection = True)
    if variant == "exp_rag":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True, use_fsp = True, fsp_k = 1,  use_reflection = True, use_rag = True)
    if variant == "exp_hi":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True, use_fsp = True, fsp_k = 1,  use_reflection = True, use_insights = True)
    if variant == "exp_hi_rag":
        return ModelerAgent(pddl_generation_model = pddl_generation_model, use_reasoning = True, reasoning_model = reasoning_model, use_objects_extraction = True, objects_extraction_model = objects_extraction_model, use_gcd = True, use_daps = True, use_comments = True, use_fsp = True, fsp_k = 1,  use_reflection = True, use_insights = True, use_rag = True)