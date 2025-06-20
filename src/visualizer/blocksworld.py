"""
Blocksworld Simulator with PDDL parsing, plan execution, and visual state rendering.
"""
import re
import os
from typing import Set, Tuple, Optional, Dict, Callable, List
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def split_pddl_problem_sections(pddl: str) -> dict:
    """
    Dado un string PDDL de problema, devuelve un diccionario con las partes:
    prefix, init, middle, goal, suffix.
    """
    # Buscar la apertura de (:init
    init_start = re.search(r':init', pddl)
    if not init_start:
        raise ValueError("No se encontró sección :init en el problema.")

    # Buscar la apertura de (:goal
    goal_start = re.search(r':goal', pddl)
    if not goal_start:
        raise ValueError("No se encontró sección :goal en el problema.")
    
    # Encontrar el primer predicado después de :init
    init_predicates_start = pddl.find("(", init_start.end())

    parens_balance = 1
    # Encontrar (and dentro de :goal
    and_match = re.search(r'and', pddl[goal_start.end():])
    if not and_match:
        # raise ValueError("No se encontró (and dentro de :goal.")
        and_start_abs = goal_start.end() - len("(and")
    else:
        and_start_abs = goal_start.end() + and_match.start()

    # El primer predicado dentro de (and
    goal_predicates_start = pddl.find("(", and_start_abs + len("(and"))

    if goal_predicates_start == -1:
        raise ValueError("No se encontraron predicados dentro de goal.")

    # Cortar prefix e init
    prefix = pddl[:init_predicates_start]
    rest_after_prefix = pddl[init_predicates_start:goal_start.start()]
    middle_start = rest_after_prefix.rfind(")") + init_predicates_start
    init_content = pddl[init_predicates_start:middle_start].strip()
    middle = pddl[middle_start:goal_predicates_start].rstrip()

    # Ahora en rest_after_middle vamos a contar paréntesis
    rest_after_middle = pddl[goal_predicates_start:]
    
    goal_end_idx = None
    for idx, char in enumerate(rest_after_middle):
        if char == '(':
            parens_balance += 1
        elif char == ')':
            parens_balance -= 1

        if parens_balance == 0 and idx > 0:
            goal_end_idx = idx
            break

    if goal_end_idx is None:
        raise ValueError("No se pudo encontrar el final de la sección goal balanceando paréntesis.")

    goal_content = rest_after_middle[:goal_end_idx].strip()
    suffix = rest_after_middle[goal_end_idx:].strip()

    return prefix, init_content, middle, goal_content, suffix

# ----- State Representation -----
class State:
    def __init__(self,
                 objects: Set[str],
                 clear: Set[str],
                 on_table: Set[str],
                 arm_empty: bool,
                 holding: Optional[str],
                 on: Set[Tuple[str, str]]):
        self.objects = set(objects)
        self.clear = set(clear)
        self.on_table = set(on_table)
        self.arm_empty = arm_empty
        self.holding = holding
        self.on = set(on)

    def is_true(self, pred: str, args: Tuple[str, ...]) -> bool:
        if pred == 'clear': return args[0] in self.clear
        if pred == 'on-table': return args[0] in self.on_table
        if pred == 'arm-empty': return self.arm_empty
        if pred == 'holding': return self.holding == args[0]
        if pred == 'on': return (args[0], args[1]) in self.on
        return False

    def copy(self) -> 'State':
        return State(self.objects, self.clear, self.on_table,
                     self.arm_empty, self.holding, self.on)

    def __repr__(self) -> str:
        return (f"State(clear={self.clear}, on_table={self.on_table}, arm_empty={self.arm_empty}, "
                f"holding={self.holding}, on={self.on})")

# ----- Action Definitions -----
class Action:
    def __init__(self,
                 name: str,
                 precond: Callable[['State', Tuple[str, ...]], bool],
                 effect : Callable[['State', Tuple[str, ...]], None]):
        self.name = name
        self.precond = precond
        self.effect = effect

    def applicable(self, state: State, args: Tuple[str, ...]) -> bool:
        return self.precond(state, args)

    def apply(self, state: State, args: Tuple[str, ...]) -> State:
        new_state = state.copy()
        self.effect(new_state, args)
        return new_state

# Preconditions & Effects
# pickup(?ob)
def pre_pickup(s: State, args):
    (ob,) = args
    return s.is_true('clear', (ob,)) and s.is_true('on-table', (ob,)) and s.is_true('arm-empty', ())
def eff_pickup(s: State, args):
    (ob,) = args
    s.holding = ob
    s.arm_empty = False
    s.clear.discard(ob)
    s.on_table.discard(ob)
pickup = Action('pickup', pre_pickup, eff_pickup)
# putdown(?ob)
def pre_putdown(s: State, args):
    (ob,) = args
    return s.is_true('holding', (ob,))
def eff_putdown(s: State, args):
    (ob,) = args
    s.clear.add(ob)
    s.on_table.add(ob)
    s.arm_empty = True
    s.holding = None
putdown = Action('putdown', pre_putdown, eff_putdown)
# stack(?ob,?under)
def pre_stack(s: State, args):
    ob, under = args
    return s.is_true('holding', (ob,)) and s.is_true('clear', (under,))
def eff_stack(s: State, args):
    ob, under = args
    s.on.add((ob, under))
    s.clear.add(ob)
    s.clear.discard(under)
    s.arm_empty = True
    s.holding = None
stack = Action('stack', pre_stack, eff_stack)
# unstack(?ob,?under)
def pre_unstack(s: State, args):
    ob, under = args
    return s.is_true('on', (ob, under)) and s.is_true('clear', (ob,)) and s.is_true('arm-empty', ())
def eff_unstack(s: State, args):
    ob, under = args
    s.on.discard((ob, under))
    s.clear.add(under)
    s.holding = ob
    s.clear.discard(ob)
    s.arm_empty = False
unstack = Action('unstack', pre_unstack, eff_unstack)

ACTIONS: Dict[str, Action] = {
    'pickup': pickup,
    'putdown': putdown,
    'stack': stack,
    'unstack': unstack,
}

# ----- PDDL Parsing Utilities -----
def parse_problem(file_path: str) -> State:
    """
    Reads a PDDL problem file and returns the initial State.
    Assumes a simple syntax with (:objects ...) and (:init ...)
    """
    with open(file_path) as f:
        text = f.read().lower()
    # Extract objects
    objs = set(re.findall(r'\(:objects([^\)]+)\)', text)[0].split())
    # Extract init predicates

    prefix, init_content, middle, goal_content, suffix = split_pddl_problem_sections(text)
    init_block = init_content

    clear, on_table, on = set(), set(), set()
    arm_empty = False
    holding = None
    for pred in re.findall(r'\(([^)]+)\)', init_block):
        parts = pred.split()
        if parts[0] == 'clear': clear.add(parts[1])
        if parts[0] == 'on-table': on_table.add(parts[1])
        if parts[0] == 'arm-empty': arm_empty = True
        if parts[0] == 'holding': holding = parts[1]
        if parts[0] == 'on': on.add((parts[1], parts[2]))
    return State(objects=set(objs), clear=clear, on_table=on_table,
                 arm_empty=arm_empty, holding=holding, on=on)

def parse_plan(file_path: str) -> List[Tuple[str, Tuple[str, ...]]]:
    """
    Reads a PDDL plan (list of actions) and returns a sequence.
    Format: one action per line: (action arg1 arg2)
    """
    seq = []
    with open(file_path) as f:
        for line in f:
            line = line.strip().strip('()').lower()
            if not line or line.startswith(';'): continue
            parts = line.split()
            name, args = parts[0], tuple(parts[1:])
            seq.append((name, args))
    return seq

# ----- Execution & Visualization -----


import pygame
import os
from typing import List, Tuple
from copy import deepcopy

BLOCK_COLORS = {
    '1': (255, 0, 0),     # Red
    '2': (0, 0, 255),     # Blue
    '3': (0, 200, 0),     # Green
    '4': (200, 200, 0),   # Yellow
    '5': (150, 0, 150),   # Purple
    '6': (100, 100, 100), # Gray
}

BLOCK_SIZE = (60, 60)
SCREEN_SIZE = (800, 600)
FPS = 60

def build_plan_trace(state, plan, actions):
    trace = [deepcopy(state)]
    current = state
    for act_name, args in plan:
        if not actions[act_name].applicable(current, args):
            raise ValueError(f"Invalid step: {act_name} {args}")
        current = actions[act_name].apply(current, args)
        trace.append(deepcopy(current))
    return trace

def visualize_pygame(trace: List, title="Blocksworld"):
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)
    step = 0

    def draw_state(state, step):
        screen.fill((255, 255, 255))
        margin = 100
        spacing = 120
        y_offset = SCREEN_SIZE[1] - 100
        stacks = {}

        # Build stacks
        for obj in state.on_table:
            stacks[obj] = [obj]
        added = True
        while added:
            added = False
            for (b, under) in state.on:
                for base in stacks:
                    if under == stacks[base][-1] and b not in stacks[base]:
                        stacks[base].append(b)
                        added = True

        # Draw stacks
        for i, base in enumerate(sorted(stacks)):
            x = margin + i * spacing
            for j, blk in enumerate(stacks[base]):
                # color = (int(blk[1])*20, 0, 0)
                color = BLOCK_COLORS[blk[1]]
                rect = pygame.Rect(x, y_offset - (j+1)*BLOCK_SIZE[1], *BLOCK_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 2)
                text = font.render(blk.upper(), True, (255, 255, 255))
                screen.blit(text, (rect.x + 20, rect.y + 5))

        # Draw arm state
        arm_text = "Arm: empty" if state.arm_empty else f"Arm: holding {state.holding.upper()}"
        text = font.render(f"Step {step} - {arm_text}", True, (0, 0, 0))
        screen.blit(text, (10, 10))

        # If holding a block, show it in the air
        if not state.arm_empty:
            blk = state.holding
            color = BLOCK_COLORS[blk[1]]
            rect = pygame.Rect(SCREEN_SIZE[0]//2 - BLOCK_SIZE[0]//2, 100, *BLOCK_SIZE)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            text = font.render(blk.upper(), True, (255, 255, 255))
            screen.blit(text, (rect.x + 20, rect.y + 5))

    # Main loop
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and step < len(trace) - 1:
                    step += 1
                elif event.key == pygame.K_LEFT and step > 0:
                    step -= 1

        draw_state(trace[step], step)
        pygame.display.flip()

    pygame.quit()

# Usage example
if __name__ == '__main__':

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    problem_path = os.path.join(BASE_DIR, 'blocks_problem.pddl')
    plan_path = os.path.join(BASE_DIR, 'blocks_plan.txt')

    initial_state = parse_problem(problem_path)
    plan = parse_plan(plan_path)
    trace = build_plan_trace(initial_state, plan, ACTIONS)
    visualize_pygame(trace)
