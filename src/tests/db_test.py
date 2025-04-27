import sqlite3
import pandas as pd
import json
import random
import os
from typing import List, Tuple

import sqlite3
import json
import random
from typing import List, Tuple

def select_and_save_planetarium_subset_sql_(
    db_path: str,
    init_goal_pairs: List[Tuple[str, str]],
    N: int,
    subset_name: str,
    seed: int = 42,
    include_splits: bool = False
) -> str:
    """
    Extrae desde SQLite un subconjunto muestreado del dataset Planetarium,
    aplicando filtros por init/goal, tamaño y abstracción, y guardándolo
    en JSON. Todo el trabajo pesado de filtrado y muestreo ocurre en SQL.

    Args:
      db_path: ruta a dataset-v2.db
      init_goal_pairs: lista de (init_str, goal_str)
      N: máximo de ejemplos por combinación
      subset_name: nombre para el archivo JSON resultante
      seed: semilla para RANDOM() de SQLite
      include_splits: si True sólo toma IDs marcados train/test en la tabla splits
    """
    random.seed(seed)
    conn = sqlite3.connect(db_path)
    # “sqlite3” no pasa seed a RANDOM(), así que mezclaremos filas en Python si quieres reproducibilidad absoluta:
    conn.execute(f"PRAGMA case_sensitive_like = OFF;")
    cursor = conn.cursor()

    # Opcionalmente, hacemos JOIN con splits para quedarnos sólo en train+test
    join_clause = ""
    if include_splits:
        join_clause = """
          JOIN splits s
            ON p.id = s.problem_id
           AND s.split_name IN ('train','test')
        """

    # Rango de parámetros
    obj_ranges    = [(1, 5), (6, 15), (16, 30), (31, 45), (45, 1000)]
    init_ranges   = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 1000)]
    goal_ranges   = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 1000)]
    init_abs_opts = [0, 1]
    goal_abs_opts = [0, 1]

    results = []

    for init_val, goal_val in init_goal_pairs:
        for o_lo, o_hi in obj_ranges:
            for i_lo, i_hi in init_ranges:
                for g_lo, g_hi in goal_ranges:
                    for init_abs in init_abs_opts:
                        for goal_abs in goal_abs_opts:
                            # Construimos WHERE y sus parámetros
                            where_sql = """
                              p.init           = ?
                              AND p.goal       = ?
                              AND p.num_objects BETWEEN ? AND ?
                              AND p.init_num_propositions BETWEEN ? AND ?
                              AND p.goal_num_propositions BETWEEN ? AND ?
                              AND p.init_is_abstract = ?
                              AND p.goal_is_abstract = ?
                            """
                            params = [
                                init_val, goal_val,
                                o_lo, o_hi,
                                i_lo, i_hi,
                                g_lo, g_hi,
                                init_abs, goal_abs,
                            ]

                            # Consulta con muestreo por RANDOM() y LIMIT
                            query = f"""
                              SELECT p.*
                                FROM problems p
                              {join_clause}
                               WHERE {where_sql}
                            ORDER BY RANDOM()
                               LIMIT ?
                            """
                            params.append(N)

                            cursor.execute(query, params)
                            cols = [c[0] for c in cursor.description]
                            rows = cursor.fetchall()

                            # Empaquetar en dicts
                            for r in rows:
                                results.append(dict(zip(cols, r)))

    conn.close()

    # Guardar JSON
    filename = f"planetarium_subset_{subset_name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f">>> Guardado {len(results)} ejemplos en {filename}")
    return filename

def select_and_save_planetarium_subset_sql(
    db_path: str,
    init_goal_pairs: List[Tuple[str, str]],
    N: int,
    subset_name: str,
    seed: int = 42,
    include_splits: bool = False
) -> str:
    """
    Selecciona subconjuntos del dataset Planetarium (train + test) desde SQLite,
    cumpliendo las combinaciones de rangos y flags de abstracción, muestreando
    hasta N ejemplos por cada (init, goal), y guarda el resultado en un JSON.

    Parámetros:
    - db_path: ruta al dataset-v2.db
    - init_goal_pairs: [(init_str, goal_str), ...]
    - N: número máximo de ejemplos por combinación
    - subset_name: identificador del subconjunto (usa en el filename)
    - seed: semilla aleatoria
    - include_splits: si True, fusiona sólo los IDs de train+test usando la
      tabla `splits`; si False, usa TODO el `problems` table.
    """
    # 1) Cargar problemas
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM problems;", conn)

    if include_splits:
        # leer la tabla splits (debe tener columnas split_name, split, problem_id)
        df_s = pd.read_sql_query("SELECT * FROM splits;", conn)
        # quedarnos sólo con train+test (ajusta según tu esquema real)
        df_ids = df_s[df_s['split_name'].isin(['train','test'])]
        df = df[df['id'].isin(df_ids['problem_id'])]
    conn.close()

    print(df)
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
        print(init_val, goal_val)
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
train_subset, test_subset = select_random_init_goal_pairs()
print("Train subset:")
print(json.dumps(train_subset, indent=2))

print("\nTest subset:")
print(json.dumps(test_subset, indent=2))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "dataset-v2.db")

select_and_save_planetarium_subset_sql(
    db_path = db_path,
    init_goal_pairs = test_subset,
    N = 1,
    subset_name = "test2",
    seed = 42,
    include_splits = False
) 

# -----------------------------------------------------

# for split in ["train","test"]:
#     mp = {}
#     s = {""}
#     print(split)
#     for x in dataset[split]:
#         for l,r in [(1,20),(21,40),(41,60),(61,80),(81,1000)]:
#             if l<=x["init_num_propositions"] and x["init_num_propositions"]<=r:
#                 init_r = (l,r)
#                 break

#         for l,r in [(1,20),(21,40),(41,60),(61,80),(81,1000)]:
#             if l<=x["goal_num_propositions"] and x["goal_num_propositions"]<=r:
#                 goal_r = (l,r)
#                 break

#         for l,r in [(1,5),(6,15),(16,30),(31,45),(45,1000)]:
#             if l<=x["num_objects"] and x["num_objects"]<=r:
#                 obj_r = (l,r)
#                 break

#         key = (x["domain"],x["init"],x["goal"],obj_r,x["init_is_abstract"],init_r,x["goal_is_abstract"],goal_r)
        
#         s.add((x["domain"],x["init"],x["goal"]))
#         if key in mp:
#             mp[key].append(x)
#         else:
#             mp[key] = [x]

#     # for k in mp:
#     #     print(k,len(mp[k]))
#     print(len(mp))
#     print(len(s))

#     mp = {}
#     for x in s:
#         if x=="":
#             continue
#         if not x[0] in mp:
#             mp[x[0]] = {(x[1],x[2])}
#         else:
#             mp[x[0]].add((x[1],x[2]))

#     for x in mp:
#         print(x,len(mp[x]))
#         for y in mp[x]:
#             print(y)

# print(dataset)
# print()
# print()
# print(dataset["train"])
# print()
# print()
# print(dataset["train"][0])

# Specify the file path for the JSON file
# file_path = "planetarium_dataset.json"

# # Create a list to store the examples as dictionaries
# dataset_list = []

# # Iterate through the splits (e.g., 'train', 'test') in the DatasetDict
# for split_name, split_dataset in dataset.items():
#     # Iterate through the examples in the dataset
#     for example in split_dataset:
#         # Add the split name to the example dictionary (optional, but useful)
#         example['split'] = split_name
#         dataset_list.append(example)

# # Save the list of dictionaries to a JSON file
# with open(file_path, "w") as f:
#     json.dump(dataset_list, f, indent=4)  # indent for pretty formatting

# print(f"Dataset saved to {file_path}")