import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET = ['work_time', 'commit_style', 'social_style', 'language_concentration']

system_prompt = """
You are the "Lead Pixel Character Designer" for a casual project called 'Git-bti'.
Your sole responsibility is to analyze the developer's profile and generate the 'character description parts' for an image prompt.
Do NOT include general art styles like "pixel art" or "chibi" in your output. The style will be applied externally. Focus only on the character's visual elements.

[INPUT VARIABLES]
- Username: {username}
- Type: {dev_type} (e.g., N-B-I-S)
- Role: {role_en}
- Description : {description}
- Main Language: {main_lang}
- Active Hours: {work_time} (Night/Day)
- Commit Style: {commit_style} (Atom/Bulk)
- Social Style: {social_style} (Crew/Indie)
- Concentration: {language_concentration} (Specialist/Generalist

[VISUAL MAPPING LOGIC (Focus on Subject Matter)]
1. Main Language (The Held Item):
   - Python: holding a cute green coiled snake staff
   - JavaScript/TypeScript: holding a glowing yellow lightning bolt wand
   - Java: holding a large brown coffee mug hammer
   - C/C++: holding dual pixelated swords

2. Active Hours: Night (N)/Day (D): 

3. Commit Style: Atom (A)/ Bulk (B)

4. Social Style : Crew (C)/Indie (I)

5. Concentration :Specialist (S)/Generalist (G)
   
[OUTPUT FORMAT]
Output ONLY a JSON object:
{{
  "role_kr": {role_kr},
  "role_en" : {role_en},
  "type": "{dev_type}",
  "description": "description": {description},
  "image_prompt_content": "A detailed description of the character elements ONLY based on logic. (e.g., 'A character wearing a dark hooded cloak with moon motifs, holding a green snake staff with both hands, standing calmly, smiling gently, holding a large glowing staff, utility belt with pouches')"
}}
"""

def prompt_generator(result):

    """
    prompt_generator의 Docstring
    
    :param result: 
    work_time : {'train': 'Day', 'percent': 61, 'description': 'Day 성향이 61% 입니다.'}
    commit_style : {'trait': 'Bulk', 'percent': 52, 'description': 'Bulk 성향이 52% 입니다.'}
    social_style : {'trait': 'Crew', 'percent': 75, 'description': 'Crew 성향이 75% 입니다.'}
    language_concentration: {'trait': 'Specialist', 'percent': 51, 'description': 'Specialist 성향이 51% 입니다.', 'top_languages': [{'name': 'HTML', 'percent': 66.3}, {'name': 'Kotlin', 'percent': 14.1}, {'name': 'Java', 'percent': 13.5}]}

    """

    # JSON 파일 경로 설정 (절대 경로 사용)
    json_path = os.path.join(os.path.dirname(__file__), 'gitbti_doc.json')

    # 파일 존재 확인
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Required configuration file not found: {json_path}")

    # JSON 파일 로드
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            gitbti_docs = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in gitbti_doc.json: {str(e)}")

    load_dotenv()

    # GEMINI API KEY 검증
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # result로부터 유형 뽑기
    type_string = "".join([result[key]['trait'][0].upper() for key in TARGET])
    result['dev_type'] = type_string

    # git-bti document로 부터 정해진 role, description 가져오기
    type_doc = next((gitbti_doc for gitbti_doc in gitbti_docs if gitbti_doc['type'] == type_string), None)

    # type_doc이 None인 경우 처리
    if not type_doc:
        raise ValueError(f"Unknown developer type: {type_string}. Please check gitbti_doc.json configuration.")

    # 프롬프트 내용 채우기
    filled_prompt = system_prompt.format(
        username=result['user_name'],
        main_lang=result['language_concentration'].get('top_languages', []),
        dev_type=result['dev_type'],

        # 개발 성향
        work_time=result['work_time'],
        commit_style=result['commit_style'],
        social_style=result['social_style'],
        language_concentration=result['language_concentration'],

        # 개발 성향 이름, 설명
        role_kr = type_doc['role']['kr'],
        role_en = type_doc['role']['en'],
        description = type_doc['description']
    )

    try:
        # --- B. Gemini에게 요청 ---
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=filled_prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json" # ★ 핵심: Gemini에게 JSON만 뱉으라고 강제함
            )
        )

        # 응답 검증
        if not response or not hasattr(response, 'text') or not response.text:
            raise ValueError("Empty response from Gemini API")

        # --- C. 결과 파싱 ---
        try:
            result_json = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}")

        result_json['role_kr'] = type_doc['role']['kr']
        result_json['role_en'] = type_doc['role']['en']
        result_json['description'] = type_doc['description']

        # --- D. stats 필드 추가 ---
        result_json['stats'] = {
            "dayVsNight": result['work_time'].get('day_percent', 50),
            "steadyVsBurst": result['commit_style'].get('atom_percent', 50),
            "indieVsCrew": result['social_style'].get('crew_percent', 50),
            "specialVsGeneral": result['language_concentration'].get('specialist_percent', 50)
        }

        return result_json

    except json.JSONDecodeError as e:
        print(f"Gemini JSON 파싱 에러: {e}")
        # 에러 시 기본값 반환 (해커톤 시연 멈춤 방지)
    except Exception as e:
        print(f"Gemini API 호출 중 에러 발생: {e}")
        # 에러 시 기본값 반환 (해커톤 시연 멈춤 방지)
        return {
            "role_kr": "알 수 없는 모험가",
            "role_en": "Unknown Adventurer",
            "type": "NBIG",
            "stats": {
                "dayVsNight": result.get('work_time', {}).get('percent', 50),
                "steadyVsBurst": result.get('commit_style', {}).get('percent', 50),
                "indieVsCrew": result.get('social_style', {}).get('percent', 50),
                "specialVsGeneral": result.get('language_concentration', {}).get('percent', 50)
            },
            "description": "데이터를 불러오는 데 실패했습니다.",
            "image_prompt": "A pixel art glitch screen, error message style"
        }