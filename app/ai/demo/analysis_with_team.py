my_gbti = "NACS"
one_person_gbti = "NBIG"
two_person_gbti = "DBIG"
three_person_gbti = "NBCG"
four_person_gbti = "DAIS"
five_person_gbti = "DBCS"

person_message_list = [one_person_gbti, two_person_gbti, three_person_gbti, four_person_gbti, five_person_gbti]

import openai
import json
client = openai.OpenAI()


content = f"""
one_person_gbti: {one_person_gbti}
two_person_gbti: {two_person_gbti}
three_person_gbti: {three_person_gbti}
four_person_gbti: {four_person_gbti}
five_person_gbti: {five_person_gbti}

my_message: {my_gbti}
"""
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": (
                "gbti의 활동 시간대에 따른 분류는 N,D로 분류하고, N은 밤에 일하는 성향을 나타내고, D는 낮에 일하는 성향을 나타낸다."
                "gbti의 커밋 패턴에 따른 분류는 A,D이고, A는 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, B는 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성격이다."
                "gbti의 작업 성향에 따른 분류는 C,I이고, C는 크루 성향을 나타내고, I는 인디 성향을 나타낸다."
                "gbti의 언어 성향에 따른 분류는 S,G이고, S는 전문가 성향을 나타내고, G는 일반인 성향을 나타낸다."
                "gbti란 각 성향의 알파벳을 합쳐서 하나의 단어로 만든 것이고, 그 단어는 모든 성향을 종합적으로 나타내는 것이다."
                "예를 들어, NACS 성향은, 밤에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "예를 들어, NBIG 성향은, 낮에 일하는 성향이고, 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성향이고, 크루 성향을 나타내고, 언어 성향이 일반인 성향을 나타낸다."
                "예를 들어, NBCG 성향은, 낮에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "예를 들어, DAIS 성향은, 밤에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 일반인 성향을 나타낸다."
                "예를 들어, DBCS 성향은, 낮에 일하는 성향이고, 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "예를 들어, NACS 성향은, 밤에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "예를 들어, NBIG 성향은, 낮에 일하는 성향이고, 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성향이고, 크루 성향을 나타내고, 언어 성향이 일반인 성향을 나타낸다."
                "예를 들어, NBCG 성향은, 낮에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "예를 들어, DAIS 성향은, 밤에 일하는 성향이고, 커밋 성향이 조금의 변경도 바로 커밋하는 성향이고, 크루 성향을 나타내고, 언어 성향이 일반인 성향을 나타낸다."
                "예를 들어, DBCS 성향은, 낮에 일하는 성향이고, 커밋 성향이 커밋 한번에 많은 양의 변경을 하는 성향이고, 크루 성향을 나타내고, 언어 성향이 전문가 성향을 나타낸다."
                "총 16가지 조합이 가능하다."
                "너는 개발자 간 성향 비교 전문가이다. "
                "다른 모든 사람과의 gbti를 비교하여 각각 그 개발자와의 성향 궁합을 판단하라. "
                "반드시 JSON 형식으로만 출력하라."
                "궁합 결과는 한 문장으로 말하라. "
            )
        },
        {
            "role": "user",
            "content": f"""
            
다음 사람들과 궁합을 판단하라.

사람에 대한 정보:
{content}

다음 형식으로 출력하라:
{{
        "first_person_compatibility": "첫번째 사람과의 궁합 결과를 한 문장으로 말하라. ",
        "two_person_compatibility": "두번째 사람과의 궁합 결과를 한 문장으로 말하라. ",
        "third_person_compatibility": "세번째 사람과의 궁합 결과를 한 문장으로 말하라. ",
        "fourth_person_compatibility": "네번째 사람과의 궁합 결과를 한 문장으로 말하라. ",
        "five_person_compatibility": "다섯번째 사람과의 궁합 결과를 한 문장으로 말하라. ",
}}
"""
        }
    ],
    temperature=0
)

generation_prompt = response.choices[0].message.content

generation_dict = json.loads(generation_prompt)

print("GPT-4o-mini 궁합 결과 \n", generation_dict)





