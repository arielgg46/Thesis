# from exp.insights_extraction import _parse_operations, parse_operations, extract_insights, load_insights
# from agents.insights_agent import get_insights_str
# from agents.modeler_agents import get_modeler_agent, ModelerAgent
# from config import LLM_DEFAULT_MODEL

# resp = """ADD: Aguacata.
# REMOVE 4: waos."""
# oper = _parse_operations(resp)
# print(oper)

# print()

# resp = """DOMAIN_KNOWLEDGE ADD 1: Aguacata.
# DOMAIN_KNOWLEDGE REMOVE 4: waos.
# GENERAL EDIT 5: life.
# GENERAL ADD 6: xd. ok ariel.
# GENERAL AGREE 6: xd.
# DOMAIN_RULES ADD 4: aiganiurulsaicalem."""
# oper = parse_operations(resp)
# print(oper)

# insights = load_insights()
# agent = ModelerAgent(LLM_DEFAULT_MODEL, True, LLM_DEFAULT_MODEL, True, LLM_DEFAULT_MODEL, True, True, 1, True, True, True, True)
# agent.set_domain("blocksworld")
# print(agent.get_insights_str())

#########################################
# from rag.retriever import Retriever

# retriever = Retriever()

# st = retriever.get_top_similar_successes(390, 2)

# for t in st:
#     print(t["id"])
#########################################
# from utils.io_utils import save_data_to_json

# import json, os

# B = {
#     "task": {"id":19014,
#     "name":"blocksworld_staircase_to_tower_blocks_list_1_1_1_1_3_3",
#     "domain":"blocksworld",
#     "init":"staircase",
#     "goal":"tower",
#     "num_objects":10,
#     "problem_pddl":"(define (problem staircase_to_tower_1_1_1_1_3_3)\n    (:domain blocksworld)\n    (:requirements :strips)\n    (:objects b1 b10 b2 b3 b4 b5 b6 b7 b8 b9)\n    (:init (arm-empty) (clear b1) (clear b2) (clear b4) (clear b7) (on b2 b3) (on b4 b5) (on b5 b6) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b1) (on-table b10) (on-table b3) (on-table b6))\n    (:goal (and (arm-empty) (clear b1) (on-table b1) (clear b2) (on-table b2) (clear b3) (on-table b3) (clear b4) (on-table b4) (clear b5) (on b5 b6) (on b6 b7) (on-table b7) (clear b8) (on b8 b9) (on b9 b10) (on-table b10)))\n)",
#     "natural_language":"You have 10 blocks, b1 through b10, stacked into 4 stacks of increasing heights, starting with a stack of height 1.\nYour goal is to have the following:\nYour arm should be empty.\nb1 should be clear.\nb1 should be on the table.\nb2 should be clear.\nb2 should be on the table.\nb3 should be clear.\nb3 should be on the table.\nb4 should be clear.\nb4 should be on the table.\nb5 should be clear.\nb5 should be on b6.\nb6 should be on b7.\nb7 should be on the table.\nb8 should be clear.\nb8 should be on b9.\nb9 should be on b10.\nb10 should be on the table.",
#     "init_is_abstract":1,
#     "init_num_propositions":15,
#     "goal_is_abstract":0,
#     "goal_num_propositions":17,
#     "is_placeholder":1
#   },
#   "trial": 1,
#   "reflection_on_previous_trial": "",
#   "agent_resp": {
#     "reasoning": """- Objects: 10 blocks, b1, b2, ..., b10.
# - Initial state: the 10 blocks are stacked into 4 stacks of increasing heights, starting with a stack of height 1. Since the description does not specify the precise configuration of blocks within each stack, we can assume any valid arrangement. For example, one possible configuration is: [b1], [b2, b3], [b4, b5, b6], and [b7, b8, b9, b10]. Here, each bracketed list represents a stack, with the first element on the table, subsequent elements stacked on top of the previous one, and the last element clear (e.g., (on-table b4), (on b5 b4), (on b6 b5), (clear b6)).
# - Goal state: The goal is fully specified and unambiguous. We translate each condition into its corresponding predicate (e.g., "Your arm should be empty." -> (arm-empty), "b1 should be clear." -> (clear b1), ..., "b9 should be on b10." -> (on b9 b10), "b10 should be on the table." -> (on-table b10)).""",
#     "objects": [
#       "b1",
#       "b2",
#       "b3",
#       "b4",
#       "b5",
#       "b6",
#       "b7",
#       "b8",
#       "b9",
#       "b10"
#     ],
#     "problem_pddl": """(define (problem blocksworld_fsp_example_problem)
#     (:domain blocksworld)
#     (:requirements :strips)
#     (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
#     (:init 
#         ; Arm state
#         (arm-empty)
#         ; 1 block stack
#         (clear b1) (on-table b1)
#         ; 2 blocks stack
#         (clear b2) (on b2 b3) (on-table b3)
#         ; 3 blocks stack
#         (clear b4) (on b4 b5) (on b5 b6) (on-table b6)
#         ; 4 blocks stack
#         (clear b7) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b10)
#     )
#     (:goal (and
#         ; Direct translation of the goal's natural language description to predicates
#         (arm-empty)
#         (clear b1) (on-table b1)
#         (clear b2) (on-table b2)
#         (clear b3) (on-table b3)
#         (clear b4) (on-table b4)
#         (clear b5) (on b5 b6) (on b6 b7) (on-table b7)
#         (clear b8) (on b8 b9) (on b9 b10) (on-table b10)
#     ))
# )"""
#   },
#   "eval": {
#       "parseable": True,
#       "solvable": True,
#       "correct": True,
#       "feedback": []
#   }
# }

# G = {
#     "task": {"id":156118,
#     "name":"gripper_holding_to_holding_balls_in_grippers_1_1_1_1_0_balls_in_rooms_1_0",
#     "domain":"gripper",
#     "init":"holding",
#     "goal":"holding",
#     "num_objects":12,
#     "problem_pddl":"(define (problem holding_to_holding_2_5)\n    (:domain gripper)\n    (:requirements :strips)\n    (:objects ball1 ball2 ball3 ball4 ball5 gripper1 gripper2 gripper3 gripper4 gripper5 room1 room2)\n    (:init (at ball5 room1) (at-robby room1) (ball ball1) (ball ball2) (ball ball3) (ball ball4) (ball ball5) (carry ball1 gripper1) (carry ball2 gripper2) (carry ball3 gripper3) (carry ball4 gripper4) (free gripper5) (gripper gripper1) (gripper gripper2) (gripper gripper3) (gripper gripper4) (gripper gripper5) (room room1) (room room2))\n    (:goal (and (carry ball1 gripper1) (carry ball2 gripper2) (carry ball3 gripper3) (carry ball4 gripper4) (free gripper5)))\n)",
#     "natural_language":"You have 2 rooms, 5 balls, and 5 grippers. 4 balls are distributed across the same number of grippers, and the rest are in the first room. The robby is in the first room.\nYour goal is to have the following:\nGripper gripper1 should be carrying ball1.\nGripper gripper2 should be carrying ball2.\nGripper gripper3 should be carrying ball3.\nGripper gripper4 should be carrying ball4.\ngripper5 should be free.",
#     "init_is_abstract":1,
#     "init_num_propositions":18,
#     "goal_is_abstract":0,
#     "goal_num_propositions":5,
#     "is_placeholder":1
#   },
#   "trial": 1,
#   "reflection_on_previous_trial": "",
#   "agent_resp": {
#     "reasoning": """- Objects: 4 rooms: room1, room2, room3 and room4; 8 balls: ball1, ball2, ..., ball8; 5 grippers: gripper1, gripper2, ..., gripper5.
# - Initial state: The description states "You have 4 rooms, 8 balls, and 5 grippers" so we must make use of the domain predicates to declare the type of each object: (room room1), ..., (room room4), (ball ball1), ..., (ball ball8), (gripper gripper1), ..., (gripper gripper5). Also "The balls are equally distributed across the rooms", this means that, because there are 4 rooms and 8 balls, there should be 8 / 4 = 2 balls in each room. Since the description does not specify the precise configuration of the balls within each room, we can assume any valid valid arrangement. For example, one possible configuration is: [ball1, ball2] at room1, [ball3, ball4] at room2, [ball5, ball6] at room3, and [ball7, ball8] at room4. This is translated to (at ball1 room1), (at ball2 room1), ..., (at ball7 room4), (at ball8 room4). "The grippers are free" and "The robby is in the first room" can be translated directly to (free gripper1), ..., (free gripper5), and (at-robby room1).
# - Goal state: The goal is fully specified and unambiguous. We translate each condition into its corresponding predicate (e.g., "Gripper gripper1 should be carrying ball1." -> (carry ball1 gripper1), ..., "Gripper gripper4 should be carrying ball4." -> (carry ball4 gripper4), "gripper5 should be free." -> (free gripper5)).""",
#     "objects": [
#         "room1",
#         "room2",
#         "room3",
#         "room4",
#         "ball1",
#         "ball2",
#         "ball3",
#         "ball4",
#         "ball5",
#         "ball6",
#         "ball7",
#         "ball8",
#         "gripper1",
#         "gripper2",
#         "gripper3",
#         "gripper4",
#         "gripper5"],
#     "problem_pddl": """(define (problem evenly_distributed_to_holding_4_8)
#     (:domain gripper)
#     (:requirements :strips)
#     (:objects room1 room2 room3 room4 ball1 ball2 ball3 ball4 ball5 ball6 ball7 ball8 gripper1 gripper2 gripper3 gripper4 gripper5)
#     (:init
#         ; 4 Rooms
#         (room room1) (room room2) (room room3) (room room4)
#         ; 8 Balls
#         (ball ball1) (ball ball2) (ball ball3) (ball ball4)
#         (ball ball5) (ball ball6) (ball ball7) (ball ball8)
#         ; 5 Grippers
#         (gripper gripper1) (gripper gripper2) (gripper gripper3) (gripper gripper4) (gripper gripper5)
#         ; Equally distributed balls in rooms: 2 balls per room
#         (at ball1 room1) (at ball2 room1)
#         (at ball3 room2) (at ball4 room2)
#         (at ball5 room3) (at ball6 room3)
#         (at ball7 room4) (at ball8 room4)
#         ; Grippers state: all free
#         (free gripper1) (free gripper2) (free gripper3) (free gripper4) (free gripper5)
#         ; Robot location
#         (at-robby room1)
#     )
#     (:goal (and
#         ; Direct translation of the goal's natural language description to predicates
#         (carry ball1 gripper1) (carry ball2 gripper2) (carry ball3 gripper3) (carry ball4 gripper4) 
#         (free gripper5)
#     ))
# )"""
#   },
#   "eval": {
#       "parseable": True,
#       "solvable": True,
#       "correct": True,
#       "feedback": []
#   }
# }

# F = {
#   "task": {
#     "id":165182,
#     "name":"floor-tile_rings_to_paint_all_grid_size_3_3_n_colors_2_n_robots_1_n_tiles_9_robot_data_{'color': 0, 'pos': [0, 0]}",
#     "domain":"floor-tile",
#     "init":"rings",
#     "goal":"paint_all",
#     "num_objects":12,
#     "problem_pddl":"(define (problem rings_to_paint_all_1_9_2)\n    (:domain floor-tile)\n    (:requirements :typing)\n    (:objects color1 color2 - color robot1 - robot tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 - tile)\n    (:init (available-color color1) (available-color color2) (right tile2 tile1) (right tile3 tile2) (right tile5 tile4) (right tile6 tile5) (right tile8 tile7) (right tile9 tile8) (robot-at robot1 tile1) (robot-has robot1 color1) (up tile1 tile4) (up tile2 tile5) (up tile3 tile6) (up tile4 tile7) (up tile5 tile8) (up tile6 tile9))\n    (:goal (and (painted tile1 color1) (painted tile2 color1) (painted tile3 color1) (painted tile4 color1) (painted tile5 color2) (painted tile6 color1) (painted tile7 color1) (painted tile8 color1) (painted tile9 color1)))\n)",
#     "natural_language":"You have 2 colors and 9 unpainted tiles arranged in a 3x3 grid, in 2 rings. The first robot is at the the top-left corner of the first ring from the outside, and has the first color. All colors are available.\nYour goal is to have the following:\nTile tile1 should be painted with color color1.\nTile tile2 should be painted with color color1.\nTile tile3 should be painted with color color1.\nTile tile4 should be painted with color color1.\nTile tile5 should be painted with color color2.\nTile tile6 should be painted with color color1.\nTile tile7 should be painted with color color1.\nTile tile8 should be painted with color color1.\nTile tile9 should be painted with color color1.",
#     "init_is_abstract":1,
#     "init_num_propositions":16,
#     "goal_is_abstract":0,
#     "goal_num_propositions":9,
#     "is_placeholder":1
#   },
#   "trial": 1,
#   "reflection_on_previous_trial": "",
#   "agent_resp": {
#     "reasoning": """- Objects: 2 colors: color1 and color2; 9 tiles: tile1. tile2, ..., tile9; only mentions one robot "The first robot": robot1.
# - Initial state: The description states that 9 unpainted tiles are arranged in a 3x3 grid, in 2 rings. Since the 9 tiles are unpainted, there will not be any predicate for painted tiles. Since it does not specify how the tiles are arranged, we can assume any valid configuration of a 3x3 grid. For example, one possible configuration is:
# [tile1, tile2, tile3],
# [tile4, tile5, tile6],
# [tile7, tile8, tile9]
# Here, each bracketed list represents a row of the grid, and is easy to derive the predicates that define this grid: By rows, first row gives predicates (right tile2 tile1) (right tile3 tile2), second row gives (right tile5 tile4) (right tile6 tile5), and third row gives (right tile8 tile7) (right tile9 tile8). By columns, first column gives (up tile1 tile4) (up tile4 tile7), second column gives (up tile2 tile5) (up tile5 tile8), and third column gives (up tile3 tile6) (up tile6 tile9). Furthermore, from the 2 rings mentioned, the second ring from the outside consists only of tile5, and the rest of the tiles make the first ring from the outside. "The first robot is at the the top-left corner of the first ring from the outside", this means that robot1 is at tile1, because it is at the intersection of the first row and first column, so (robot-at robot1 tile1), "and has the first color" means robot1 has the color1, so (robot-has robot1 color1). "All colors are available", so (available-color color1) and (available-color color2).
# - Goal state: The goal is fully specified and unambiguous. We translate each condition into its corresponding predicate (e.g., "Tile tile1 should be painted with color color1." -> (painted tile1 color1), ..., "Tile tile4 should be painted with color color1." -> (painted tile4 color1), "Tile tile5 should be painted with color color2." -> (painted tile5 color2), ...).""",
#     "objects": {
#         "color": [
#             "color1",
#             "color2"
#         ],
#         "robot": [
#             "robot1"
#         ],
#         "tile": [
#             "tile1",
#             "tile2",
#             "tile3",
#             "tile4",
#             "tile5",
#             "tile6",
#             "tile7",
#             "tile8",
#             "tile9"
#         ]
#     },
#     "problem_pddl": """(define (problem floor_tile_fsp_example_problem)
#     (:domain floor-tile)
#     (:requirements :typing)
#     (:objects color1 color2 - color tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 - tile robot1 - robot)
#     (:init
#         ; Row 1
#         (right tile2 tile1) (right tile3 tile2)
#         ; Row 2
#         (right tile5 tile4) (right tile6 tile5)
#         ; Row 3
#         (right tile8 tile7) (right tile9 tile8)
#         ; Column 1
#         (up tile1 tile4) (up tile4 tile7)
#         ; Column 2
#         (up tile2 tile5) (up tile5 tile8)
#         ; Column 3
#         (up tile3 tile6) (up tile6 tile9)
#         ; Robot 1
#         (robot-at robot1 tile1) (robot-has robot1 color1)
#         ; Available colors
#         (available-color color1) (available-color color2))
#     (:goal (and
#         ; Direct translation of the goal's natural language description to predicates
#         (painted tile1 color1) (painted tile2 color1) (painted tile3 color1)
#         (painted tile4 color1) (painted tile5 color2) (painted tile6 color1)
#         (painted tile7 color1) (painted tile8 color1) (painted tile9 color1)
#     ))
# )"""
#   },
#   "eval": {
#       "parseable": True,
#       "solvable": True,
#       "correct": True,
#       "feedback": []
#   }
# }

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# exps_path = os.path.join(BASE_DIR, "exp", "exps")

# save_data_to_json(B, os.path.join(exps_path, "task_19014_trial_1.json"))
# save_data_to_json(G, os.path.join(exps_path, "task_156118_trial_1.json"))
# save_data_to_json(F, os.path.join(exps_path, "task_165182_trial_1.json"))

# from utils.evaluation_utils import eval_trial

# task = {
#     "domain": "blocksworld",
#     "problem_pddl": """(define (problem blocksworld_fsp_example_problem)
#     (:domain blocksworld)
#     (:requirements :strips)
#     (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
#     (:init (arm-empty) (clear b1) (clear b2) (clear b4) (clear b7) (on b2 b3) (on b4 b5) (on b5 b6) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b1) (on-table b10) (on-table b3) (on-table b6))
#     (:goal (and (arm-empty) (clear b1) (on-table b1) (clear b2) (on-table b2) (clear b3) (on-table b3) (clear b4) (on-table b4) (clear b5) (on b5 b6) (on b6 b7) (on-table b7) (clear b8) (on b8 b9) (on b9 b10) (on-table b10)))
# )""",
#     "is_placeholder": True
# }

# modeling_agent_resp = {
#     "problem_pddl": """(define (problem blocksworld_fsp_example_problem)
#     (:domain blocksworld)
#     (:requirements :strips)
#     (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
#     (:init (arm-empty) (not (clear b1)) (clear b2) (clear b4) (clear b7) (on b2 b3) (on b4 b5) (on b5 b6) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b1) (on-table b10) (on-table b3) (on-table b6))
#     (:goal (and (arm-empty) (clear b1) (on-table b1) (clear b2) (on-table b2) (clear b3) (on-table b3) (clear b4) (on-table b4) (clear b5) (on b5 b6) (on b6 b7) (on-table b7) (clear b8) (on b8 b9) (on b9 b10) (on-table b10)))
# )"""
# }

# task = {
#     "domain": "floor-tile",
#     "problem_pddl": """(define (problem floor_tile_fsp_example_problem)
#     (:domain floor-tile)
#     (:requirements :typing)
#     (:objects color1 color2 - color tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 - tile robot1 - robot)
#     (:init (right tile2 tile1) (right tile3 tile2) (right tile5 tile4) (right tile6 tile5) (right tile8 tile7) (right tile9 tile8) (up tile1 tile4) (up tile4 tile7) (up tile2 tile5) (up tile5 tile8) (up tile3 tile6) (up tile6 tile9) (robot-at robot1 tile1) (robot-has robot1 color1) (available-color color1) (available-color color2))
#     (:goal (and (painted tile1 color1) (painted tile2 color1) (painted tile3 color1) (painted tile4 color1) (painted tile5 color2) (painted tile6 color1) (painted tile7 color1) (painted tile8 color1) (painted tile9 color1)))
# )""",
#     "is_placeholder": True
# }

# modeling_agent_resp = {
#     "problem_pddl": """(define (problem floor_tile_fsp_example_problem)
#     (:domain floor-tile)
#     (:requirements :typing)
#     (:objects color1 color2 - color tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 - tile robot1 - robot)
#     (:init (right tile2 tile1) (right tile3 tile2) (right tile5 tile4) (right tile6 tile5) (right tile8 tile7) (right tile9 tile8) (up tile1 tile4) (up tile4 tile7) (up tile2 tile5) (up tile5 tile8) (up tile3 tile6) (up tile6 tile9) (robot-at robot1 tile1) (available-color color1) (available-color color2))
#     (:goal (and (painted tile1 color1) (painted tile2 color1) (painted tile3 color1) (painted tile4 color1) (painted tile5 color2) (painted tile6 color1) (painted tile7 color1) (painted tile8 color1) (painted tile9 color1)))
# )"""
# }

# print(eval_trial(task, modeling_agent_resp))

# ----------

# from utils.pddl_utils import split_pddl_problem_sections
from utils.evaluation_utils import eval_trial

problem_pddl = """
(define (problem blocksworld_fsp_example_problem)
    (:domain blocksworld)
    (:requirements :strips)
    (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
    (:init 
        ; Arm state
        (arm-empty)
        ; 1 block stack
        (clear b1) (on-table b1)
        ; 2 blocks stack
        (clear b2) (on b2 b3) (on-table b3)
        ; 3 blocks stack
        (clear b4) (on b4 b5) (on b5 b6) (on-table b6)
        ; 4 blocks stack
        (clear b7) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b10)
    )
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates
        (arm-empty)
        (clear b1) (on-table b1)
        (clear b2) (on-table b2)
        (clear b3) (on-table b3)
        (clear b4) (on-table b4)
        (clear b5) (on b5 b6) (on b6 b7) (on-table b7)
        (clear b8) (on b8 b9) (on b9 b10) (on-table b10)
    ))
)"""

task = {
    "domain": "gripper",
    "problem_pddl": problem_pddl,
    "is_placeholder": 0
}

modeling_agent_resp = {
    "problem_pddl": 
"""
(define (problem blocksworld_fsp_example_problem)
    (:domain blocksworld)
    (:requirements :strips)
    (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
    (:init 
        ; Arm state
        (arm-empty)
        ; 1 block stack
        (clear b1) (on-table b1)
        ; 2 blocks stack
        (clear b2) (on b2 b3) (on-table b3)
        ; 3 blocks stack
        (clear b4) (on b4 b5) (on b5 b6) (on-table b6)
        ; 4 blocks stack
        (clear b7) (on b7 b8) (on b8 b9) (on b9 b10) (on-table b10)
    )
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates
        (arm-empty)
        (clear b1) (on-table b1)
        (clear b2) (on-table b2)
        (clear b3) (on-table b3)
        (clear b4) (on-table b4)
        (clear b5) (on b5 b6) (on b6 b7) (on-table b7)
        (clear b8) (on b8 b9) (on b9 b10) (on-table b10)
    ))
)"""
}

print(eval_trial(task, modeling_agent_resp))