import os
from typing import Any, Dict, List
import numpy as np

from rag.api_embedder import get_task_embedding
from exp.experience_pool import get_successful_trials
from config import EMBEDDINGS_TRAINING_SUBSET, EMBEDDINGS_TESTING_SUBSET

class Retriever:
    """
    Module for RAG
    """
    def __init__(
        self
    ):
        ids_train, embeddings_train = self.load_ids_and_embeddings(EMBEDDINGS_TRAINING_SUBSET)
        ids_test, embeddings_test = self.load_ids_and_embeddings(EMBEDDINGS_TESTING_SUBSET)
        max_id = max(ids_train + ids_test)

        self.embeddings = [None] * (max_id + 1)
        for i in range(len(ids_train)):
            self.embeddings[ids_train[i]] = embeddings_train[i]
        for i in range(len(ids_test)):
            self.embeddings[ids_test[i]] = embeddings_test[i]

    def load_ids_and_embeddings(self, subset_name):
        # Later: load
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        embeddings_path = os.path.join(BASE_DIR, f'embeddings_with_ids_{subset_name}.npz')
        loaded = np.load(embeddings_path, allow_pickle=True)
        ids = loaded['ids'].tolist()
        embeddings = loaded['embeddings']

        return ids, embeddings

    def retrieve_similar_tasks_ids(self, k: int, embeddings, ids, problem_id: int = None, problem_nl: str = None, problem_nl_embedding = None) -> List[Dict[str, Any]]:
        """
        Given a problem, return the top-k experiences
        whose problem_nl is most similar (by cosine similarity).
        """

        if embeddings is None:
            return []
        
        if problem_nl_embedding is None:
            problem_nl_embedding = self.embeddings[problem_id]
            if problem_nl_embedding is None:
                print(f"Embedding not precomputed for task with id {problem_id}.")
                problem_nl_embedding = get_task_embedding(problem_nl)
            
        # cosine similarity = dot product when embeddings L2-normalized
        sims = embeddings @ problem_nl_embedding
        # get top-k indices (desc order)
        topk_idx = np.argsort(sims)[-k:][::-1]
        return [ids[i] for i in topk_idx]

    def get_top_similar_successes(self, query_id, k):
        successful_trials = get_successful_trials()

        id_to_trial = {}
        for trial in successful_trials:
            id = trial["task"]["id"]
            id_to_trial[id] = trial

        succ_ids = [trial["task"]["id"] for trial in successful_trials]
        succ_embeddings = []
        for id in succ_ids:
            succ_embeddings.append(self.embeddings[id])

        top_k = self.retrieve_similar_tasks_ids(k, succ_embeddings, succ_ids, query_id)
        similar_tasks = []
        for id in top_k:
            similar_tasks.append(id_to_trial[id])

        return similar_tasks