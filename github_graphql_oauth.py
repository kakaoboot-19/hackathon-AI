"""
GitHub OAuth + GraphQL Raw Data 수집 서버

실행 방법:
1. pip install fastapi uvicorn requests --break-system-packages
2. GitHub App 설정:
   - https://github.com/settings/developers 접속
   - "New OAuth App" 클릭
   - Application name: "GitHub Character Test"
   - Homepage URL: http://localhost:8000
   - Authorization callback URL: http://localhost:8000/callback
   - 생성 후 Client ID와 Client Secret 복사
3. 아래 CLIENT_ID, CLIENT_SECRET 수정
4. uvicorn github_graphql_oauth:app --reload
5. 브라우저에서 http://localhost:8000 접속
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import requests
import json
import os
from datetime import datetime

app = FastAPI()

# ============================================
# 🔧 여기에 GitHub OAuth App 정보 입력!
# ============================================
CLIENT_ID = "Ov23liUVYHSBSinAaFay"  # GitHub OAuth App의 Client ID
CLIENT_SECRET = "def6c11d4c54264e38dd2a70698cb1ced9da6902"  # GitHub OAuth App의 Client Secret
# ============================================

REDIRECT_URI = "http://localhost:8000/callback"
DATA_DIR = "github_graphql_raw_data"

# 데이터 저장 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home():
    """홈페이지 - GitHub 로그인 버튼"""
    return """
    <html>
        <head>
            <title>GitHub GraphQL 데이터 수집</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }
                .login-btn {
                    background-color: #24292e;
                    color: white;
                    padding: 15px 30px;
                    font-size: 18px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }
                .login-btn:hover {
                    background-color: #444;
                }
                .info {
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #f6f8fa;
                    border-radius: 5px;
                    text-align: left;
                }
            </style>
        </head>
        <body>
            <h1>🚀 GitHub GraphQL 데이터 수집기</h1>
            <p>GitHub OAuth로 로그인하여 GraphQL 데이터를 수집합니다</p>
            
            <a href="/login" class="login-btn">
                🔐 GitHub로 로그인
            </a>
            
            <div class="info">
                <h3>📊 수집 가능한 데이터:</h3>
                <ul>
                    <li>사용자 프로필 정보</li>
                    <li>레포지토리 목록 + 언어 분포</li>
                    <li>커밋 히스토리 (시간, 추가/삭제 라인 수)</li>
                    <li>기여 통계</li>
                    <li>이슈/PR 활동</li>
                    <li>📄 README.md 파일</li>
                </ul>
                <p><strong>저장 위치:</strong> github_graphql_raw_data/</p>
            </div>
        </body>
    </html>
    """


@app.get("/login")
async def login():
    """GitHub OAuth 로그인 페이지로 리다이렉트"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=read:user,public_repo"  # public_repo만 접근 (private 제외)
    )
    return RedirectResponse(github_auth_url)


@app.get("/callback")
async def callback(code: str):
    """GitHub OAuth 콜백 - 토큰 발급"""
    
    # 1. code를 access_token으로 교환
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"}
    )
    
    token_data = token_response.json()
    
    if "access_token" not in token_data:
        return JSONResponse({
            "error": "토큰 발급 실패",
            "details": token_data
        }, status_code=400)
    
    access_token = token_data["access_token"]
    
    # 2. 토큰으로 사용자 정보 조회
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"}
    )
    user_data = user_response.json()
    username = user_data.get("login", "unknown")
    
    # 3. GraphQL로 데이터 수집
    graphql_data = collect_graphql_data(access_token, username)
    
    # 4. 데이터 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DATA_DIR}/{username}_{timestamp}_graphql.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(graphql_data, f, indent=2, ensure_ascii=False)
    
    # 5. 결과 페이지
    return HTMLResponse(f"""
    <html>
        <head>
            <title>수집 완료</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 50px auto;
                    padding: 20px;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                pre {{
                    background-color: #f6f8fa;
                    padding: 20px;
                    border-radius: 5px;
                    overflow-x: auto;
                    max-height: 600px;
                    overflow-y: auto;
                }}
                .btn {{
                    background-color: #0366d6;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✅ 데이터 수집 완료!</h2>
                <p>사용자: <strong>{username}</strong></p>
                <p>저장 파일: <strong>{filename}</strong></p>
            </div>
            
            <h3>📄 수집된 Raw JSON 데이터:</h3>
            <pre>{json.dumps(graphql_data, indent=2, ensure_ascii=False)}</pre>
            
            <a href="/" class="btn">🏠 홈으로 돌아가기</a>
        </body>
    </html>
    """)


def collect_graphql_data(token: str, username: str):
    """GraphQL API로 데이터 수집"""
    
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # GraphQL 쿼리
    query = """
    query($username: String!) {
      user(login: $username) {
        login
        name
        bio
        company
        location
        email
        createdAt
        followers {
          totalCount
        }
        following {
          totalCount
        }
        
        repositories(first: 10, orderBy: {field: UPDATED_AT, direction: DESC}) {
          totalCount
          nodes {
            name
            description
            createdAt
            updatedAt
            stargazerCount
            forkCount
            primaryLanguage {
              name
              color
            }
            
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
            
            readme: object(expression: "HEAD:README.md") {
              ... on Blob {
                text
                byteSize
              }
            }
            
            defaultBranchRef {
              name
              target {
                ... on Commit {
                  history(first: 30) {
                    totalCount
                    edges {
                      node {
                        committedDate
                        message
                        additions
                        deletions
                        author {
                          name
                          email
                          date
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        
        contributionsCollection {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
        
        issues(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
          totalCount
          nodes {
            title
            createdAt
            state
            comments {
              totalCount
            }
          }
        }
        
        pullRequests(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
          totalCount
          nodes {
            title
            createdAt
            state
            additions
            deletions
            comments {
              totalCount
            }
          }
        }
      }
      
      rateLimit {
        limit
        remaining
        resetAt
      }
    }
    """
    
    variables = {"username": username}
    
    response = requests.post(
        url,
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    return response.json()


if __name__ == "__main__":
    import uvicorn
    print("""
    ============================================
    🚀 GitHub GraphQL 데이터 수집 서버 시작
    ============================================
    
    ⚠️  시작하기 전에:
    1. CLIENT_ID와 CLIENT_SECRET을 설정했는지 확인하세요!
    2. GitHub OAuth App 설정:
       - https://github.com/settings/developers
       - New OAuth App 클릭
       - Callback URL: http://localhost:8000/callback
    
    📌 접속 주소: http://localhost:8000
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)