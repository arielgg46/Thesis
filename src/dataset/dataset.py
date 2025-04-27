from datasets import load_dataset, load_from_disk, Dataset
from typing import List, Tuple
import pandas as pd
import json
import os
import random

# dataset = load_dataset("BatsResearch/planetarium")
# dataset.save_to_disk("planetarium_local")
# dataset = load_from_disk("planetarium_local")

def select_and_save_planetarium_subset(
    dataset_path: str,
    init_goal_pairs: list,
    N: int,
    subset_name: str,
    seed: int = 42
) -> str:
    """
    Selecciona subconjuntos del dataset Planetarium (train + test) cumpliendo las combinaciones
    de rangos y flags de abstracción, muestreando hasta N ejemplos por cada combinación de
    (init, goal), y guarda el resultado en un JSON.

    Parámetros:
    - dataset_path: ruta donde se guardó con save_to_disk (p.ej. "planetarium_local")
    - init_goal_pairs: lista de tuplas [(init_str, goal_str), ...]
    - N: número máximo de ejemplos a tomar por combinación
    - subset_name: nombre identificador del subconjunto
    - seed: semilla de aleatoriedad

    Retorna:
    - Nombre del archivo JSON donde se guardó el subconjunto.
    """
    # Carga y concatenación de splits
    ds = load_from_disk(dataset_path)
    df_train = pd.DataFrame(ds['train'])
    df_test  = pd.DataFrame(ds['test'])
    df = pd.concat([df_train, df_test]).reset_index(drop=True)
    
    # Definición de rangos
    obj_ranges    = [(1, 5), (6, 15), (16, 30), (31, 45), (45, 1000)]
    init_ranges   = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 1000)]
    goal_ranges   = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 1000)]
    init_abs_opts = [0, 1]
    goal_abs_opts = [0, 1]
    
    random.seed(seed)
    selected = []

    # Iterar todas las combinaciones solicitadas
    for init_val, goal_val in init_goal_pairs:
        for o_lo, o_hi in obj_ranges:
            for i_lo, i_hi in init_ranges:
                for g_lo, g_hi in goal_ranges:
                    for init_abs in init_abs_opts:
                        for goal_abs in goal_abs_opts:
                            mask = (
                                (df['init'] == init_val) &
                                (df['goal'] == goal_val) &
                                df['num_objects'].between(o_lo, o_hi) &
                                df['init_num_propositions'].between(i_lo, i_hi) &
                                df['goal_num_propositions'].between(g_lo, g_hi) &
                                (df['init_is_abstract'] == init_abs) &
                                (df['goal_is_abstract'] == goal_abs)
                            )
                            subset = df[mask]
                            if not subset.empty:
                                k = min(N, len(subset))
                                sampled = subset.sample(n=k, random_state=seed)
                                selected.append(sampled)
    
    if selected:
        result_df = pd.concat(selected).reset_index(drop=True)
    else:
        result_df = pd.DataFrame(columns=df.columns)
    
    # Guardar en JSON
    filename = f"planetarium_subset_{subset_name}.json"
    result_df.to_json(filename, orient="records", indent=2)
    
    return filename

# Ejemplo de uso:
# init_goal_list = [
#     ('on_table', 'stack'), ('stack', 'holding_one'),
#     ('grid', 'paint_all'), ('swap', 'swap')
# ]
# json_file = select_and_save_planetarium_subset(
#     dataset_path="planetarium_local",
#     init_goal_pairs=init_goal_list,
#     N=2,
#     subset_name="ejemplo_test"
# )
# print(f"Subconjunto guardado en: {json_file}")

def load_planetarium_subset(subset_name):
    """
    Loads a previously saved subset of the Planetarium dataset from JSON
    and returns it as a Hugging Face Dataset object.

    Args:
        subset_name (str): Name used to save the subset JSON file.

    Returns:
        Dataset: Hugging Face Dataset object containing the subset.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filename = f"planetarium_subset_{subset_name}.json"
    subset_path = os.path.join(BASE_DIR, "subsets", filename)
    with open(subset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return Dataset.from_list(data)

# Ejemplo de uso:
# subset = load_planetarium_subset("ejemplo_test")
# print(subset)
# print(subset[0])

def select_random_init_goal_pairs(
    train_frac: float = 1/3,
    test_frac: float = 1/2,
    random_seed: int = 42
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    random.seed(random_seed)

    # Definición estática de los pares init-goal
    train_pairs = [
        # gripper
        ('evenly_distributed', 'one_room'),
        ('holding', 'pickup'),
        ('one_room', 'n_room_distributed'),
        ('one_room', 'evenly_distributed'),
        ('evenly_distributed', 'pickup'),
        ('one_room', 'focus_max'),
        ('holding', 'evenly_distributed'),
        ('holding', 'n_room_distributed'),
        ('n_room_distributed', 'holding'),
        ('holding', 'focus_max'),
        ('evenly_distributed', 'evenly_distributed'),
        ('evenly_distributed', 'n_room_distributed'),
        ('n_room_distributed', 'one_room'),
        ('holding', 'one_room'),
        ('n_room_distributed', 'pickup'),
        ('one_room', 'holding'),
        ('one_room', 'one_room'),
        ('n_room_distributed', 'evenly_distributed'),
        ('one_room', 'pickup'),
        ('holding', 'holding'),
        ('n_room_distributed', 'n_room_distributed'),
        ('n_room_distributed', 'focus_max'),
        ('evenly_distributed', 'holding'),
        # blocksworld
        ('staircase', 'stack'),
        ('on_table', 'equal_towers'),
        ('tower', 'on_table'),
        ('staircase', 'on_table'),
        ('holding_one', 'equal_towers'),
        ('tower', 'equal_towers'),
        ('holding_one', 'stack'),
        ('stack', 'holding_one'),
        ('equal_towers', 'holding_one'),
        ('staircase', 'equal_towers'),
        ('equal_towers', 'staircase'),
        ('stack', 'staircase'),
        ('on_table', 'staircase'),
        ('stack', 'tower'),
        ('equal_towers', 'tower'),
        ('holding_one', 'staircase'),
        ('tower', 'holding_one'),
        ('on_table', 'tower'),
        ('tower', 'staircase'),
        ('staircase', 'holding_one'),
        ('staircase', 'staircase'),
        ('holding_one', 'tower'),
        ('tower', 'tower'),
        ('equal_towers', 'stack'),
        ('staircase', 'tower'),
        ('stack', 'stack'),
        ('stack', 'on_table'),
        ('equal_towers', 'on_table'),
        ('on_table', 'stack'),
        ('stack', 'equal_towers'),
        ('equal_towers', 'equal_towers'),
        ('tower', 'stack'),
    ]

    test_pairs = [
        # floor-tile
        ('grid', 'all_different'),
        ('rings', 'paint_x'),
        ('grid', 'checkerboard'),
        ('grid', 'paint_all'),
        ('rings', 'checkerboard'),
        ('disconnected_rows', 'disconnected_rows'),
        ('rings', 'rings'),
        ('rings', 'paint_all'),
        ('grid', 'paint_x'),
        # gripper
        ('swap', 'swap'),
        ('holding', 'focus_min'),
        ('holding', 'drop_and_pickup'),
        ('one_room', 'drop_and_pickup'),
        ('one_room', 'focus_min'),
        ('n_room_distributed', 'focus_min'),
        ('juggle', 'juggle'),
        # blocksworld
        ('swap', 'swap'),
        ('invert', 'invert'),
    ]

    n_train = int(len(train_pairs) * train_frac)
    n_test = int(len(test_pairs) * test_frac)

    selected_train = random.sample(train_pairs, n_train)
    selected_test = random.sample(test_pairs, n_test)

    return selected_train, selected_test

# Ejemplo de uso:
# train_subset, test_subset = select_random_init_goal_pairs()
# print("Train subset:")
# print(json.dumps(train_subset, indent=2))

# print("\nTest subset:")
# print(json.dumps(test_subset, indent=2))