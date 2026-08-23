import re
import os
import json

def clean_and_check_farsi(text):
    has_farsi = re.search(r'[\u0600-\u06FF]', text)
    if has_farsi:
        cleaned = re.sub(r"[^\u0600-\u06FF\s]", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if len(cleaned) > 0 else None
    else:
        return text.strip() if len(text.strip()) > 0 else None

def extract_like_count(like_str):
    if isinstance(like_str, int):
        return like_str
    if not like_str:
        return 0
    match = re.search(r"[\d,]+", like_str)
    if match:
        return int(match.group(0).replace(",", ""))
    return 0

def load_updated_posts(file_path):
    if not os.path.exists(file_path):
        print(f"⚠️ File {file_path} not found.")
        return []
    updated = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                parts = line.strip().split("|")
                if len(parts) == 2:
                    username = parts[0].strip()
                    post_url = parts[1].strip()
                    updated.append((username, post_url))
    return updated

def load_last_state(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_state(file_path, state):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def save_post_data(file_path, data):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
