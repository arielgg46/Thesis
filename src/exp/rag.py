from embeddings.api_embedder import get_task_embedding
from embeddings.retriever import get_loaded_embedding, retrieve_similar_tasks_ids, load_ids_and_embeddings
from dataset.dataset import load_planetarium_subset
from exp.experience_pool import get_successful_trials

def get_top_similar_successes(query_id, subset_name, k):
    ids, embeddings = load_ids_and_embeddings(subset_name)
    for i in range(len(ids)):
        if ids[i] == query_id:
            query_emb = embeddings[i]
            break

    successful_trials = get_successful_trials()

    succ_ids = [trial["task"]["id"] for trial in successful_trials]
    succ_embeddings = [embeddings[i] for i in range(len(embeddings)) if ids[i] in succ_ids]

    top_k = retrieve_similar_tasks_ids(succ_ids, succ_embeddings, "", k, query_emb)
    similar_tasks = [trial["task"] for trial in successful_trials if trial["task"]["id"] in top_k]

    return similar_tasks