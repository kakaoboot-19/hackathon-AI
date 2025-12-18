"""GitHub API 서비스"""
import requests
# from app.config import settings
from app.ai.queries import GITHUB_QUERY


def get_github_data(username: str) -> dict:
    """
    GitHub 데이터 수집
    
    Args:
        username: GitHub 사용자 이름
        
    Returns:
        dict: GitHub GraphQL API 응답
        
    Raises:
        Exception: API 호출 실패 시
    """
    url = "https://api.github.com/graphql"

    github_token = os.getenv("GITHUB_TOKEN", "")
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        url,
        json={"query": GITHUB_QUERY, "variables": {"username": username}},
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.status_code}")
    
    data = response.json()
    
    # GraphQL 에러 체크
    if "errors" in data:
        errors = data["errors"]
        error_messages = [e.get("message", "") for e in errors]
        raise Exception(f"GraphQL Error: {', '.join(error_messages)}")
    
    # 사용자 존재 확인
    if not data.get("data", {}).get("user"):
        raise Exception(f"User not found: {username}")
    
    return data