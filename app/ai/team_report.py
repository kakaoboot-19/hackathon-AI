"""팀 리포트 생성 모듈"""
import openai
import json
import os


def generate_team_report(user_results: list) -> dict:
    """
    여러 사용자의 GBTI 결과를 받아서 팀 궁합 리포트를 생성합니다.

    Args:
        user_results: 각 사용자의 GBTI 결과 리스트
            예: [
                {"username": "user1", "type": "NACS", ...},
                {"username": "user2", "type": "DBIG", ...}
            ]

    Returns:
        dict: {
            "synergy": "시너지 평가 (3줄)",
            "warning": "위험요소 평가 (3줄)"
        }
    """

    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 사용자 정보를 텍스트로 변환 (username을 직접 사용)
    user_info_lines = []
    for result in user_results:
        username = result.get("username", "알 수 없음")
        gbti_type = result.get("type", "알 수 없음")
        user_info_lines.append(f"{username}: {gbti_type}")

    content = "\n".join(user_info_lines)

    # GPT-4o-mini API 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "gbti의 활동 시간대에 따른 분류는 N,D로 분류하고, N은 밤에 일하는 성향을 나타내고, D는 낮에 일하는 성향을 나타낸다. "
                    "gbti의 커밋 패턴에 따른 분류는 A,B이고, A는 커밋 성향이 조금의 변경도 바로 커밋하는 성향(Atom)이고, B는 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성향(Bulk)이다. "
                    "gbti의 작업 성향에 따른 분류는 C,I이고, C는 크루 성향(Crew)을 나타내고, I는 인디 성향(Indie)을 나타낸다. "
                    "gbti의 언어 성향에 따른 분류는 S,G이고, S는 전문가 성향(Specialist)을 나타내고, G는 제너럴리스트 성향(Generalist)을 나타낸다. "
                    "gbti란 각 성향의 알파벳을 합쳐서 하나의 단어로 만든 것이고, 그 단어는 모든 성향을 종합적으로 나타내는 것이다. "
                    "총 16가지 조합이 가능하다 (예: NACS, NBIG, DBCS, DAIS 등). "
                    "\n\n"
                    "너는 개발자 간 성향 비교 전문가이다. "
                    "주어진 팀원들의 gbti를 분석하여 팀 전체의 시너지와 위험요소를 파악하라. "
                    "시너지는 팀원들의 성향이 어떻게 상호보완되고 강점을 만드는지 설명하고, "
                    "위험요소는 팀원들의 성향 차이로 인해 발생할 수 있는 갈등이나 문제점을 설명하라. "
                    "\n\n"
                    "**중요**: 팀원을 언급할 때 반드시 실제 username을 사용하라. "
                    "'팀원 1', '팀원 2' 같은 표현 대신 'jmKim02', 'OhJin-Soo' 같은 실제 username을 사용하라. "
                    "\n\n"
                    "반드시 JSON 형식으로만 출력하라. "
                    "시너지와 위험요소 각각을 3줄로 작성하라."
                )
            },
            {
                "role": "user",
                "content": f"""
다음 팀원들의 궁합을 판단하라.

팀원 정보:
{content}

다음 형식으로 출력하라:
{{
    "synergy": "시너지에 대한 평가를 3줄로 말하라.",
    "warning": "위험요소에 대한 평가를 3줄로 말하라."
}}
"""
            }
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    generation_prompt = response.choices[0].message.content

    # 응답이 비어있는지 확인
    if not generation_prompt:
        raise ValueError("LLM 응답이 비어있습니다.")

    # 마크다운 코드 블록 제거 (```json ... ``` 형식)
    if generation_prompt.strip().startswith("```"):
        lines = generation_prompt.strip().split("\n")
        # 첫 줄과 마지막 줄이 ``` 로 시작/끝나면 제거
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        generation_prompt = "\n".join(lines)

    # JSON 파싱 시도
    try:
        generation_dict = json.loads(generation_prompt)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용:\n{generation_prompt}")
        raise

    print("✅ GPT-4o-mini 팀 궁합 리포트 생성 완료")
    print(f"   시너지: {generation_dict.get('synergy', 'N/A')[:50]}...")
    print(f"   위험요소: {generation_dict.get('warning', 'N/A')[:50]}...")

    return generation_dict


if __name__ == "__main__":
    # 테스트 코드
    test_users = [
        {"username": "user1", "type": "NACS"},
        {"username": "user2", "type": "DBIG"},
        {"username": "user3", "type": "DAIS"}
    ]

    result = generate_team_report(test_users)
    print("\n테스트 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
