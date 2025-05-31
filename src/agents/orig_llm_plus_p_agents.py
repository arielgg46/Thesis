from client.client import llm_query

class OrigLLMPlusPAgent:
    """
    Agent for generating PDDL problem files from natural language descriptions.
    Almost exactly like original LLM+P implementation
    """
    def __init__(
        self,
        pddl_generation_model: str,
        use_fsp: bool = False
    ):
        self.pddl_generation_model = pddl_generation_model
        self.use_fsp = use_fsp
        
        self.domain = None
        self.problem_nl = None

        if self.use_fsp:
            self.domain_instruction = {
                "blocksworld": """I want you to solve planning problems. An example planning problem is: 
 You have 5 blocks. 
b2 is on top of b5. 
b5 is on top of b1. 
b1 is on top of b4. 
b3 is on top of b2. 
b4 is on the table. 
b3 is clear. 
Your arm is empty. 
Your goal is to move the blocks. 
b4 should be on top of b3. 
The problem PDDL file to this problem is: 
 (define (problem blocksworld_fsp_example_problem)
(:domain blocksworld)
(:objects b1 b2 b3 b4 b5 )
(:init
(arm-empty)
(on b1 b4)
(on b2 b5)
(on b3 b2)
(on-table b4)
(on b5 b1)
(clear b3)
)
(:goal
(and
(on b4 b3))
)
) 
Now I have a new planning problem and its description is:""",
                "gripper": """I want you to solve planning problems. An example planning problem is: 
The robby has 2 grippers. 
There are 4 rooms and 6 balls. 
Robby is in room3. 
ball1 is in room3. ball2 is in room1. ball3 is in room3. ball4 is in room2. ball5 is in room4. ball6 is in room4. 
The grippers are free. 
Your goal is to transport the balls to their destinations. 
ball1 should be in room4. 
ball2 should be in room1. 
ball3 should be in room1. 
ball4 should be in room2. 
ball5 should be in room1. 
ball6 should be in room1. 
The problem PDDL file to this problem is: 
 (define (problem gripper_fsp_example_problem)
(:domain gripper)
(:objects gripper1 gripper2
room1 room2 room3 room4
ball1 ball2 ball3 ball4 ball5 ball6)
(:init
(gripper gripper1)
(gripper gripper2)
(room room1)
(room room2)
(room room3)
(room room4)
(ball ball1)
(ball ball2)
(ball ball3)
(ball ball4)
(ball ball5)
(ball ball6)
(free gripper1)
(free gripper2)
(at-robby room3)
(at ball1 room3)
(at ball2 room1)
(at ball3 room3)
(at ball4 room2)
(at ball5 room4)
(at ball6 room4)
)
(:goal
(and
(at ball1 room4)
(at ball2 room1)
(at ball3 room1)
(at ball4 room2)
(at ball5 room1)
(at ball6 room1)
)
)
) 
Now I have a new planning problem and its description is:""",
                "floor-tile": """I want you to solve planning problems. An example planning problem is: 
 You have 4 rows and 3 columns of unpainted floor tiles. 
tile1 tile2 tile3
tile4 tile5 tile6
tile7 tile8 tile9
tile10 tile11 tile12
You have 2 robots. 
Robot1 can paint in color color1. 
Robot2 can paint in color color2. 
robot2 is at tile8. 
robot1 is at tile1. 
Your goal is to paint the grid in the following pattern: 
tile4 is color1; tile5 is color1; tile6 is color1. 
The problem PDDL file to this problem is: 
 (define (problem floor_tile_fsp_example_problem)
 (:domain floor-tile)
 (:requirements :typing)
 (:objects 
    tile1 tile2 tile3
    tile4 tile5 tile6
    tile7 tile8 tile9
    tile10 tile11 tile12 - tile
    robot1 robot2 - robot
    color1 color2 - color
)
 (:init
   (robot-at robot1 tile1)
   (robot-has robot1 color1)
   (robot-at robot2 tile8)
   (robot-has robot2 color2)
   (available-color color1)
   (available-color color2)
   (up tile1 tile4)
   (up tile2 tile5)
   (up tile3 tile6)
   (up tile4 tile7)
   (up tile5 tile8)
   (up tile6 tile9)
   (up tile7 tile10)
   (up tile8 tile11)
   (up tile9 tile12)
   (right tile2 tile1)
   (right tile3 tile2)
   (right tile5 tile4)
   (right tile6 tile5)
   (right tile8 tile7)
   (right tile9 tile8)
   (right tile11 tile10)
   (right tile12 tile11)
)
 (:goal (and
    (painted tile4 color1)
    (painted tile5 color1)
    (painted tile6 color1)
))
)
Now I have a new planning problem and its description is:""",
            }
        else:
            self.domain_instruction = {
                "blocksworld": """The robot has four actions: pickup, putdown, stack, and unstack. The domain assumes a world where there are a set of blocks that can be stacked on top of each other, an arm that can hold one block at a time, and a table where blocks can be placed.

The actions defined in this domain include:

pickup: allows the arm to pick up a block from the table if it is clear and the arm is empty. After the pickup action, the arm will be holding the block, and the block will no longer be on the table or clear.

putdown: allows the arm to put down a block on the table if it is holding a block. After the putdown action, the arm will be empty, and the block will be on the table and clear.

stack: allows the arm to stack a block on top of another block if the arm is holding the top block and the bottom block is clear. After the stack action, the arm will be empty, the top block will be on top of the bottom block, and the bottom block will no longer be clear.

unstack: allows the arm to unstack a block from on top of another block if the arm is empty and the top block is clear. After the unstack action, the arm will be holding the top block, the top block will no longer be on top of the bottom block, and the bottom block will be clear. 
Now consider a planning problem. The problem description is:""",
                "gripper": """You are a robot with a gripper that can move objects between different rooms.

There are three actions defined in this domain:

The move action: This action allows the robot to move from one room to another.The action has a single precondition, which is that the robot is currently in a room. The effect of this action is to move the robot to another room and to remove the fact that it is in the original room.

The pick action: This action allows the robot to pick up an object using the gripper. The action has three preconditions: (1) the object is located in a room (2) the robot is currently in the same room and (3) the gripper is free (i.e., not holding any object). The effect of this action is to update the state of the world to show that the robot is carrying the object using the gripper, the object is no longer in the room, and the gripper is no longer free.

The drop action: This action allows the robot to drop an object that it is carrying. The action has two preconditions: (1) the robot is currently carrying the object using the gripper, and (2) the robot is currently in a room. The effect of this action is to update the state of the world to show that the robot is no longer carrying the object using the gripper, the object is now located in the room, and the gripper is now free. 
Now consider a planning problem. The problem description is:""",
                "floor-tile": """You control a set of robots that use different colors to paint patterns in floor tiles. The robots can move around the floor tiles in four directions (up, down, left and right). Robots paint with one color at a time, but can change their spray guns to any available color. However, robots can only paint the tile that is in front (up), behind (down), to the left, or to the right of them.  

Here are the actions each robot can do
Change the spray gun color if the new color is available
Paint the tile that is up from the robot
Paint the tile that is down from the robot
Paint the tile that is to the left of the robot
Paint the tile that is to the right of the robot
Move up
Move down
Move right
Move left

You have the following restrictions on your actions:
A robot can only paint a tile to the color of its spray gun.
Now consider a planning problem. The problem description is:""",
            }


    def set_domain(self, domain):
        if self.domain == domain:
            return
        self.domain = domain

    def set_task(self, id, domain, problem_nl):
        self.problem_id = id
        self.set_domain(domain)
        self.problem_nl = problem_nl

    def solve_task(self) -> dict:
        response = {}
        prompt_tokens = []
        completion_tokens = []
        total_tokens = []
        
        # PDDL Generation
        # System Prompt
        system_prompt = f"""{self.domain_instruction[self.domain]}

{self.problem_nl}"""
        
        # User Prompt
        user_prompt = f"""Provide me with the problem PDDL file that describes the planning problem directly without further explanations?"""

        # LLM call
        pddl_generation_resp = llm_query(system_prompt, user_prompt, self.pddl_generation_model)
        
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
        return response
    
def get_orig_llm_plus_p_agent(variant, pddl_generation_model):
    if variant == "orig_llm_plus_p":
        return OrigLLMPlusPAgent(pddl_generation_model = pddl_generation_model)
    if variant == "orig_llm_plus_p_fsp":
        return OrigLLMPlusPAgent(pddl_generation_model = pddl_generation_model, use_fsp = True)
    