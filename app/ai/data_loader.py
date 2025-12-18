# data_loader.py
import json

def load_github_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
