# llm_evaluator.py
import json
import openai

client = openai.OpenAI()

SYSTEM_PROMPT = """
너는 클라우드 엔지니어 채용 관점에서 GitHub 프로젝트를 평가하는 전문가다.
반드시 JSON 형식으로만 출력하라.
"""

def evaluate_project(analysis_result: dict, model: str) -> dict:
    content = f"""
# 평균 커밋 시간대
{analysis_result['mean_commit_hour']}

평균 커밋당 추가 코드 줄 수:
{analysis_result['mean_additions']}

주 사용 언어:
{analysis_result['primary_language']}

README:
{analysis_result['readme']}

커밋 메시지:
{analysis_result['commit_messages']}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
