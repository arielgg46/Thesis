import os
from typing import Any, Dict, List
import numpy as np

from dataset.dataset import load_planetarium_subset
from embeddings.api_embedder import get_task_embedding

def load_ids_and_embeddings(subset_name):
  # Later: load
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  embeddings_path = os.path.join(BASE_DIR, f'embeddings_with_ids_{subset_name}.npz')
  loaded = np.load(embeddings_path, allow_pickle=True)
  ids = loaded['ids'].tolist()
  embeddings = loaded['embeddings']

  return ids, embeddings

def retrieve_similar_tasks_ids(ids, embeddings, problem_nl: str, k: int = 5, query_emb = None) -> List[Dict[str, Any]]:
    """
    Given a new NL description, embed it and return the top-k experiences
    whose problem_nl is most similar (by cosine similarity).
    """
    if embeddings is None:
        return []
    if query_emb is None:
        query_emb = get_task_embedding(problem_nl)
    # cosine similarity = dot product when embeddings L2-normalized
    sims = embeddings @ query_emb
    # get top-k indices (desc order)
    topk_idx = np.argsort(sims)[-k:][::-1]
    return [ids[i] for i in topk_idx]

def get_loaded_embedding(subset_name, id):
    ids, embeddings = load_ids_and_embeddings(subset_name)
    for i in range(len(ids)):
        if ids[i] == id:
            return embeddings[i]
    print("Embedding not found")
    return None