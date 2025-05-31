from sentence_transformers import SentenceTransformer
from dataset.dataset import load_planetarium_subset
import numpy as np

model_name = 'sentence-transformers/all-mpnet-base-v2'
embedder = SentenceTransformer(model_name)

def get_task_embedding(task_nl):
  embedding = embedder.encode(task_nl, normalize_embeddings=True)
  return embedding

def save_planetarium_subset_embeddings(subset_name):
  # Load dataset
  subset = load_planetarium_subset(subset_name)
  ids = subset["id"]
  nls = subset["natural_language"]
  
  # Get embeddings
  embeddings_list = []
  for i in range(len(nls)):
    print(f"{i+1} / {len(nls)}")
    embeddings_list.append(get_task_embedding(nls[i]))
  embeddings = np.stack(embeddings_list)

  # Save
  np.savez_compressed(f'/content/gdrive/MyDrive/thesis/planetarium/planetarium/embeddings/embeddings_with_ids_{subset_name}.npz', ids=ids, embeddings=embeddings)
