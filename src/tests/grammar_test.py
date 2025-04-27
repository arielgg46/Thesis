from grammar.grammar import get_pddl_problem_grammar_daps_no_typing, get_pddl_problem_grammar_daps_typing
from domains.utils import get_domain_predicates, get_domain_types

# domain = "tile-world"
# problem = "rings_to_paint_all_1_9_2"
# domain_predicates = get_domain_predicates(domain)
# domain_types = get_domain_types(domain)
# objects = [
#     ("color", ["color1", "color2"]),
#     ("robot", ["robot1"]),
#     ("tile", ["tile1", "tile2", "tile3", "tile4", "tile5", "tile6", "tile7", "tile8", "tile9"])
# ]

# print(get_pddl_problem_grammar_daps_typing(domain, problem, domain_predicates, objects, domain_types))

# domain = "blocksworld"
# problem = "blocksworld_on_table_to_tower_blocks_list_1_1_1_2"
# domain_predicates = get_domain_predicates(domain)
# domain_types = get_domain_types(domain)
# objects = ["b1", "b2", "b3", "b4", "b5"]

# print(get_pddl_problem_grammar_daps_no_typing(domain, problem, domain_predicates, objects))

domain = "gripper"
problem = "gripper_holding_to_n_room_distributed_balls_in_grippers_0_0_balls_in_rooms_1"
domain_predicates = get_domain_predicates(domain)
domain_types = get_domain_types(domain)
objects = ["ball1", "gripper1", "gripper2", "room1"]

print(get_pddl_problem_grammar_daps_no_typing(domain, problem, domain_predicates, objects))
