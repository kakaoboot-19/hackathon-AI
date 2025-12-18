import json

with open("/Users/js/hackertone/jmKim02_20251217_142711_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 프로젝트1 주요 사용 언어
primary_language = data["data"]["user"]["repositories"]["nodes"][0]["primaryLanguage"]["name"]
#print(primary_language)

# 프로젝트1_README
project1_readme = data["data"]["user"]["repositories"]["nodes"][0]["readme"]["text"]
#print("프로젝트1_readme \n",project1_readme)


# 프로젝트1 전체 커밋 메시지            
edges = (
    data["data"]["user"]["repositories"]["nodes"][0]
    ["defaultBranchRef"]["target"]["history"]["edges"]
)

project1_commit_messages = []
for edge in edges:
    message = edge["node"].get("message")
    if message:
        #print("프로젝트1 전체 커밋 메시지: ",message)
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


commit_dates = []
for edge in edges:
    additions = edge["node"].get("committedDate")
    if additions:
        commit_dates.append(additions)


# 평균 커밋 시간대
from datetime import datetime

hours = []

for d in commit_dates:
    dt = datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
    hours.append(dt.hour)

mean_project1_commit_dates = sum(hours) / len(hours)
#print(mean_project1_commit_dates)



# GPT-4o-mini 평가
import openai
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
  "reasoning": "이 사람이 Day 성향인지, Night 성향인지 판단하는 이유",
  "commit_style": "Steady" or "Burst",
  "reasoning": "이 사람이 Steady 성향인지, Burst 성향인지 판단하는 이유",
  "readme_style": "Explainable" or "Actionable",
  "reasoning": "이 사람이 Explainable 성향인지, Actionable 성향인지 판단하는 이유",
  "language_style": "Specialist" or "Generalist",
  "reasoning": "이 사람이 Specialist 성향인지, Generalist 성향인지 판단하는 이유",
  "final_word": 각 알파벳을 조합하여 만든 단어
  "percentage": 각 특성 각각에 대한 퍼센트를 %를 붙여 말하라.
  "percentage_reasoning": 각 특성 각각에 대한 퍼센트를 말하는 이유
  "final_result": 최종 요약 결과를 한 문장으로 말하라.
}}
"""
        }
    ],
    temperature=0
)

generation_prompt = response.choices[0].message.content

generation_dict = json.loads(generation_prompt)

print("GPT-4o-mini 평가 결과 \n", generation_dict["final_result"])


final_result = generation_dict["final_result"]


from PIL import Image
from io import BytesIO

import os
import requests

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
API_TOKEN = os.getenv("HF_API")

if not API_TOKEN:
    raise RuntimeError("HF_TOKEN environment variable not set")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_image(prompt: str, output_path: str):
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt},
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

    # 🔹 bytes → PIL Image
    image = Image.open(BytesIO(response.content)).convert("RGB")

    return image







        
        