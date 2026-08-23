import os
import json

def load_json_file(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_usernames(file_path):
    if not os.path.exists(file_path):
        print(f"⚠️ File {file_path} not found.")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_updated_users(file_path, users):
    with open(file_path, "w", encoding="utf-8") as f:
        for user in users:
            f.write(user + "\n")
