import os

def save_text(file_path, content):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def make_case_dir(output_root, agent, domain, idx):
    case_dir = os.path.join(output_root, agent, f"{domain}_{idx}")
    os.makedirs(case_dir, exist_ok=True)
    return case_dir
