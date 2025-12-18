import json
import os
import requests
import openai
from datetime import datetime
from PIL import Image
from io import BytesIO


def analyze_and_generate(github_data: dict) -> dict:
    """
    GitHub 데이터를 분석하고 이미지를 생성합니다.

    Args:
        github_data: GitHub GraphQL API 응답 데이터

    Returns:
        dict: {
            "analysis": AI 분석 결과 (dict),
            "image": PIL Image 객체
        }
    """
    # 첫 번째 레포지토리 가져오기
    first_repo = github_data["data"]["user"]["repositories"]["nodes"][0]

    # 프로젝트1 주요 사용 언어 (None일 수 있음)
    primary_language_obj = first_repo.get("primaryLanguage")
    primary_language = primary_language_obj["name"] if primary_language_obj else "Unknown"

    # 프로젝트1_README (None일 수 있음)
    readme_obj = first_repo.get("readme")
    project1_readme = readme_obj["text"] if readme_obj else "No README available"

    # 프로젝트1 전체 커밋 메시지
    default_branch = first_repo.get("defaultBranchRef")
    if not default_branch or not default_branch.get("target"):
        raise ValueError("Repository has no commits or default branch")

    edges = default_branch["target"]["history"]["edges"]

    project1_commit_messages = []
    for edge in edges:
        message = edge["node"].get("message")
        if message:
            project1_commit_messages.append(message)

    # 프로젝트1 커밋당 추가 커밋 수
    project1_additions = []
    for edge in edges:
        additions = edge["node"].get("additions")
        if additions:
            project1_additions.append(additions)

    sum_project1_additions = sum(project1_additions)
    count_project1_additions = len(project1_additions)

    # 평균 커밋 수
    mean_project1_additions = sum_project1_additions / count_project1_additions

    # 커밋 날짜 수집
    commit_dates = []
    for edge in edges:
        committed_date = edge["node"].get("committedDate")
        if committed_date:
            commit_dates.append(committed_date)

    # 평균 커밋 시간대
    hours = []
    for d in commit_dates:
        dt = datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
        hours.append(dt.hour)

    mean_project1_commit_dates = sum(hours) / len(hours)

    # GPT-4o-mini 평가
    client = openai.OpenAI()

    content = f"""
# 평균 커밋 시간대
{mean_project1_commit_dates}

평균 커밋당 추가 코드 줄 수:
{mean_project1_additions}

주 사용 언어:
{primary_language}

README:
{project1_readme}

커밋 메시지:
{project1_commit_messages}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 클라우드 엔지니어 채용 관점에서 "
                    "GitHub 프로젝트를 평가하는 전문가다. "
                    "반드시 JSON 형식으로만 출력하라."
                    "평균 커밋 시간대에 따라 이 사람이 Day 성향인지, Night 성향인지 판단하라"
                    "평균 커밋당 추가 코드 줄 수를 보고 이 사람이 Steady 성향인지, Burst 성향인지 판단하라"
                    "README, 커밋 메시지를 보고 이 사람이 Explainable 성향인지, Actionable 성향인지 판단하라"
                    "주 사용 언어를 보고 이 사람이 Specialist 성향인지, Generalist 성향인지 판단하라"
                    "결론적으로 각 판단 성향의 앞글자만 따 4글자의 단어를 만들어라"
                    "예를 들어, Day 성향이면 D, Steady 성향이면 S, Explainable 성향이면 E, Specialist 성향이면 S 이렇게 4글자의 알파벳을 합치면 최종 글자는 \"DSES\"가 된다."
                    "각 특성 각각에 대한 퍼센트를 구체적으로 말하라"
                    "예시는 다음과 같다"
                    "Day 성향: 80%, Steady 성향: 70%, Explainable 성향: 60%, Specialist 성향: 50%"
                )
            },
            {
                "role": "user",
                "content": f"""
다음 프로젝트를 평가하라.

[프로젝트 정보]
{content}

다음 형식으로 출력하라:
{{
  "time_distribution": "Day" or "Night",
  "time_reasoning": "이 사람이 Day 성향인지, Night 성향인지 판단하는 이유",
  "commit_style": "Steady" or "Burst",
  "commit_reasoning": "이 사람이 Steady 성향인지, Burst 성향인지 판단하는 이유",
  "readme_style": "Explainable" or "Actionable",
  "readme_reasoning": "이 사람이 Explainable 성향인지, Actionable 성향인지 판단하는 이유",
  "language_style": "Specialist" or "Generalist",
  "language_reasoning": "이 사람이 Specialist 성향인지, Generalist 성향인지 판단하는 이유",
  "final_word": "각 알파벳을 조합하여 만든 단어",
  "percentage": "각 특성 각각에 대한 퍼센트를 %를 붙여 말하라.",
  "percentage_reasoning": "각 특성 각각에 대한 퍼센트를 말하는 이유",
  "final_result": "최종 요약 결과를 한 문장으로 말하라."
}}
"""
            }
        ],
        temperature=0
    )

    generation_prompt = response.choices[0].message.content
    generation_dict = json.loads(generation_prompt)

    print("GPT-4o-mini 평가 결과 \n", generation_dict["final_result"])

    # 이미지 생성
    final_result = generation_dict["final_result"]
    image = generate_image(final_result)

    return {
        "analysis": generation_dict,
        "image": image
    }


def generate_image(prompt: str):
    """HuggingFace API를 사용하여 이미지 생성"""
    API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    API_TOKEN = os.getenv("HF_API")
    style_prompt = "low resolution pixel art, 8-bit style sprite, Chibi pixel art, Big head small body, cute proportions, retro 1980s game graphics,Chunky pixels, Limited color palette, Simple shapes, background color code is rgba(245, 235, 210, 1),"

    if not API_TOKEN:
        raise RuntimeError("HF_API environment variable not set")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    final_prompt = f'{style_prompt},{prompt}'

    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": final_prompt},
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API error {response.status_code}: {response.text}"
        )

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type:
        raise RuntimeError(
            f"Unexpected response ({content_type}): {response.text}"
        )

    # bytes → PIL Image
    image = Image.open(BytesIO(response.content)).convert("RGB")

    return image


# 테스트용 코드 (직접 실행 시)
if __name__ == "__main__":
    import sys
    sys.path.append('/Users/pete/Documents/GitHub/hackathon-AI')
    from app.services.github_service import get_github_data

    # GitHub username 입력
    test_username = input("GitHub username을 입력하세요 (기본값: jmKim02): ").strip() or "jmKim02"

    print(f"🔍 GitHub 데이터 수집 중: {test_username}")
    github_data = get_github_data(test_username)

    print("🤖 AI 분석 및 이미지 생성 중...")
    result = analyze_and_generate(github_data)

    print("\n✅ 분석 완료!")
    print(f"   타입: {result['analysis']['final_word']}")
    print(f"   설명: {result['analysis']['final_result']}")
    print(f"   이미지 생성 완료: {result['image'].size}")
