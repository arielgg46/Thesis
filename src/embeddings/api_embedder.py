import requests

model_id = "sentence-transformers/all-mpnet-base-v2"
hf_token = "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"

api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
headers = {"Authorization": f"Bearer {hf_token}"}

def get_tasks_embeddings(texts):
    response = requests.post(api_url, headers=headers, json={"inputs": texts, "options":{"wait_for_model":True}})
    return response.json()

def get_task_embedding(text):
    response = requests.post(api_url, headers=headers, json={"inputs": text, "options":{"wait_for_model":True}})
    return response.json()