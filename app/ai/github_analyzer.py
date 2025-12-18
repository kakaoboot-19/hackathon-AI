# github_analyzer.py
from datetime import datetime

def analyze_repository(data: dict) -> dict:
    repo = data["data"]["user"]["repositories"]["nodes"][0]

    primary_language = repo["primaryLanguage"]["name"]
    readme = repo["readme"]["text"]

    edges = repo["defaultBranchRef"]["target"]["history"]["edges"]

    commit_messages = []
    additions = []
    commit_hours = []

    for edge in edges:
        node = edge["node"]

        if node.get("message"):
            commit_messages.append(node["message"])

        if node.get("additions"):
            additions.append(node["additions"])

        if node.get("committedDate"):
            dt = datetime.strptime(node["committedDate"], "%Y-%m-%dT%H:%M:%SZ")
            commit_hours.append(dt.hour)

    mean_additions = sum(additions) / len(additions)
    mean_commit_hour = sum(commit_hours) / len(commit_hours)

    return {
        "mean_commit_hour": mean_commit_hour,
        "mean_additions": mean_additions,
        "primary_language": primary_language,
        "readme": readme,
        "commit_messages": commit_messages
    }
