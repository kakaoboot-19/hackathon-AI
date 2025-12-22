"""GitHub API 서비스"""
import os
import re
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
        ValueError: 잘못된 username 입력 시
        Exception: API 호출 실패 시
    """
    # username 검증
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")

    username = username.strip()

    if not username:
        raise ValueError("Username cannot be empty or whitespace")

    # GitHub username 형식 검증 (영문, 숫자, 하이픈, 언더스코어만 허용)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValueError(f"Invalid username format: {username}. Only alphanumeric characters, hyphens, and underscores are allowed.")

    # 하이픈으로 시작하거나 끝나는 경우 차단
    if username.startswith('-') or username.endswith('-'):
        raise ValueError(f"Username cannot start or end with a hyphen: {username}")

    if len(username) > 39:  # GitHub username 최대 길이
        raise ValueError(f"Username too long: {username}. Maximum 39 characters allowed.")

    url = "https://api.github.com/graphql"

    github_token = os.getenv("GITHUB_TOKEN", "")

    # GitHub token 검증
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        url,
        json={"query": GITHUB_QUERY, "variables": {"username": username}},
        headers=headers,
        timeout=(5, 55)  # (연결 타임아웃, 읽기 타임아웃)
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