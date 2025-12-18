import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET = ['work_time', 'commit_style', 'social_style', 'language_concentration']

system_prompt = """ 
1. 활동시간대 : Night (N) 몰입형 vs ☀️ Day  (D) 루틴형 
2. 커민 패턴 : Atom (A) 파티형 vs 💥 Bulk 솔플형(B)
3. Crew  (C) 크루형 vs ⚡ Indie (I) 인디형
4. Specialist (S) 마스터형 vs 🌀 Generalist 올라운더형(G)

[입력 데이터]
- 유저명: {username}
- 유형 : {dev_type}
- 주 언어: {main_lang}
- 활동 시간 유형 : {work_time}
- 커밋 스타일 : {commit_style}
- social style : {social_style}
- language concentration : {language_concentration}

4. **image_prompt 작성 규칙 (매우 중요!):**
   - 반드시 다음 키워드 포함: "low resolution pixel art, chunky pixels, 8x8 sprite style, arcade game style, limited color palette, retro 1980s game graphics"
   - 주 언어의 상징을 시각적으로 표현:
     * Python → green snake, serpent staff
     * JavaScript → yellow lightning bolts, dynamic energy
     * Java → coffee cup, brown robes
     * TypeScript → blue magical shield, structured armor
     * Rust → iron/steel armor, gear mechanisms
     * C++ → dual swords, high-speed warrior
     * Go → blue gopher companion, simple design
     * Ruby → red gemstone staff, elegant mage
   - 플레이 스타일 반영:
   - 캐릭터는 8x8 픽셀 스프라이트 스타일로 간단하고 명확하게
   - 배경은 단순하게 (투명하거나 단색)
[JSON 출력 예시]
{{
  "role": "율법의 고위 사제 (High Priest of Order)",
  "type" : {dev_type}
  "description": "9 to 6, 완벽한 컨벤션, 칼 같은 코드 리뷰. 빛을 수호합니다.",
  "image_prompt": "low resolution pixel art, 16x16 sprite, A lone wizard character with a green snake coiled around a wooden staff, wearing dark green robes with hood, moon symbol glowing, chunky pixels, arcade style, limited color palette (4 colors: green, black, white, gray), retro 1980s game graphics, simple background"
}}

[필수 규칙]
- 반드시 JSON 형식으로만 출력할 것
- 한국어: role, skill, description
- 영어: image_prompt
- 입력된 데이터의 특징을 **최대한 활용**하여 개성 있게 만들 것!
"""

def prompt_generator(result):

    load_dotenv()
    genai.configure(api_key=GEMINI_API_KEY)

    # result로부터 유형 뽑기
    type_string = "".join([result[key]['trait'][0].upper() for key in TARGET])
    result['dev_type'] = type_string

    # 프롬프트 내용 채우
    filled_prompt = system_prompt.format(
        username=result['user_name'],
        main_lang=result['language_concentration']['top_languages'],
        dev_type=result['dev_type'],

        # 개발 성향
        work_time=result['work_time'],
        commit_style=result['commit_style'],
        social_style=result['social_style'],
        language_concentration=result['language_concentration']
    )

    try:
        # --- B. Gemini에게 요청 ---
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(
            filled_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        # --- C. 결과 파싱 ---
        # response.text에 이미 JSON 문자열이 들어있습니다.
        result_json = json.loads(response.text)
        return result_json

    except Exception as e:
        print(f"Gemini API 호출 중 에러 발생: {e}")
        # 에러 시 기본값 반환 (해커톤 시연 멈춤 방지)
        return {
            "role": "알 수 없는 모험가",
            "type": "NBIG",
            "description": "데이터를 불러오는 데 실패했습니다.",
            "image_prompt": "A pixel art glitch screen, error message style"
        }