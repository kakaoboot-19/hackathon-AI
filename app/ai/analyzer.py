import dateutil.parser
import math
from collections import defaultdict


## graphql로 받은 json 가져오는 부분 필요
def analyzer(graphql_data):
    commit_hours = []
    commit_messages = []
    additions = []
    deletions = []
    
    user_name = graphql_data['data']['user']['login']
    coll = graphql_data['data']['user']['contributionsCollection']
    repos = graphql_data['data']['user']['repositories']['nodes']
    
    for repo in repos:  # ✅ node → repo
        if not repo.get('defaultBranchRef'):
            continue
        
        edges = repo['defaultBranchRef']['target']['history']['edges']
        
        for edge in edges:
            commit = edge["node"]
            
            if commit.get("message"):
                commit_messages.append(commit["message"])
            
            if commit.get("additions"):
                additions.append(commit["additions"])
                
            if commit.get("deletions"):
                deletions.append(commit["deletions"])
            
            if commit.get("committedDate"):
                commit_hours.append(commit["committedDate"])
    
    work_time = get_time_type(commit_hours)
    commit_style = analyze_work_style(additions, deletions)
    social_style = analyze_social_style_percent(coll)
    language_concentration = analyze_entropy_concentration(repos)
    
    print(f'work_time : f"{work_time['trait']} 성향이 {work_time['percent']:.0f}% 입니다."')
    print(f'commit_style : f"{commit_style['trait']} 성향이 {commit_style['percent']:.0f}% 입니다."')
    print(f'social_style : f"{social_style['trait']} 성향이 {social_style['percent']:.0f}% 입니다."')
    print(f'language_concentration : f"{language_concentration['trait']} 성향이 {language_concentration['percent']:.0f}% 입니다."')


    return {
        'user_name': user_name,
        'work_time' : work_time,
        'commit_style' : commit_style,
        'social_style' : social_style,
        'language_concentration' : language_concentration
    }



# 활동 시간대 판단
def get_time_type(commit_timestamps):
    night_count = 0

    if not commit_timestamps:
        return "Day" # 데이터 없으면 기본값
    
    total = len(commit_timestamps)

    for commit_timestamp in commit_timestamps:
        # UTC -> KST (+9) 변환
        utc_dt = dateutil.parser.parse(commit_timestamp)
        kst_hour = (utc_dt.hour + 9) % 24
        
        # Night 기준: 19시 ~ 06시 (저녁 7시 ~ 새벽 6시)
        if 19 <= kst_hour or kst_hour < 6:
            night_count += 1
            
    night_percent = (night_count / total) * 100
    main_trait = "Night" if night_percent >= 50 else "Day"
    main_percent = night_percent if main_trait == "Night" else (100 - night_percent)

    return {
        "trait": main_trait,      
        "percent": round(main_percent)
    }

#커밋 style
def analyze_work_style(additions,deletions):
    bulk_count = 0
    
    # 기준선 (Threshold): 50줄 이상이면 Bulk로 간주
    BULK_THRESHOLD = 100 

    # 하나의 커밋당 addition + deletion을 더했을 때 100줄이 넘으면
    # addition에 커밋당 addition 수가 들어가 있음

    for add, delete in zip(additions, deletions):
        total_change = add + delete
        if total_change >= BULK_THRESHOLD: # 100줄을 넘으면 
            bulk_count += 1
        if total_change == 0:
            return {"type": "Atom", "percent": 0} 
        # 2. 퍼센트 계산
    bulk_percent = (bulk_count / len(additions)) * 100
    
    # 3. 성향 결정 (과반수 기준)
    # Bulk가 50% 이상이면 Bulk 타입, 아니면 Atom 타입
    main_trait = "Bulk" if bulk_percent >= 50 else "Atom"
    main_percent = bulk_percent if main_trait == "Bulk" else (100 - bulk_percent)
    
    return {
        "trait": main_trait,          
        "percent": round(main_percent), 
        "description": f"{main_trait} 성향이 {main_percent:.0f}% 입니다."
    }

#social style 판단
def analyze_social_style_percent(collection):
    
    # 1. Indie 활동 (Coding)
    commits = collection['totalCommitContributions']
    
    # 2. Team 활동 (Socializing)
    # PR은 혼자 할 수도 있지만, GitHub에서는 보통 협업의 시작으로 봅니다.
    reviews = collection['totalPullRequestReviewContributions']
    issues = collection['totalIssueContributions']
    prs = collection['totalPullRequestContributions']
    
    team_actions = reviews + issues + prs
    total_actions = commits + team_actions
    
    if total_actions == 0:
        return {"trait": "Indie", "percent": 0} # 활동 없으면 기본값

    # 3. 퍼센트 계산 (Indie 기준)
    indie_percent = (commits / total_actions) * 100
    crew_percent = 100 - indie_percent
    
    # 4. 성향 판정
    # 커밋이 과반수 이상이면 Indie, 아니면 Team
    # (사실상 거의 항상 Indie가 나오겠지만, Team 활동이 10%만 넘어도 '협업 지향'으로 해석 가능)
    main_trait = "Indie" if indie_percent >= 50 else "Crew"
    main_percent = indie_percent if main_trait == "Indie" else crew_percent
    
    return {
        "trait": main_trait,
        "percent": round(main_percent)
    }


## 언어 집중도 판별
import math
from collections import defaultdict

def analyze_entropy_concentration(nodes):
    # 1. 데이터 집계
    lang_stats = defaultdict(int)
    total_bytes = 0
    
    for node in nodes:
        if node['languages']['edges']:
            for edge in node['languages']['edges']:
                size = edge['size']
                lang_name = edge['node']['name']
                lang_stats[lang_name] += size
                total_bytes += size
                
    if total_bytes == 0:
        return {"trait": "Generalist", "percent": 0}

    # 언어의 종류 수 (N)
    num_languages = len(lang_stats)
    
    # 예외 처리: 언어가 딱 1개면 무조건 100% Specialist
    # 예외 처리: 언어가 딱 1개면 무조건 100% Specialist
    if num_languages == 1:
        top_lang = list(lang_stats.keys())[0]
        return {
            "trait": "Specialist", 
            "percent": 100.0,
            "top_languages": [{"name": top_lang, "percent": 100.0}]
        }

    # 2. 섀넌 엔트로피(H) 계산
    entropy = 0
    for size in lang_stats.values():
        p = size / total_bytes # 확률(비중)
        if p > 0:
            entropy -= p * math.log(p) # 자연로그 사용

    # 3. 정규화 (0 ~ 1 사이로 만들기)
    # 최대 엔트로피 = log(언어 개수)
    max_entropy = math.log(num_languages)
    
    # normalized_entropy가 1에 가까우면 Generalist, 0에 가까우면 Specialist
    normalized_entropy = entropy / max_entropy
    
    # 4. Specialist 퍼센트로 변환 (역수)
    specialist_percent = (1 - normalized_entropy) * 100
    
    # 5. 성향 판정
    main_trait = "Specialist" if specialist_percent >= 50 else "Generalist"
    main_percent = specialist_percent if main_trait == "Specialist" else (1-specialist_percent)

    # ✅ 6. Top 3 언어 추출
    top_3 = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    top_languages = [
        {
            "name": lang, 
            "percent": round((size / total_bytes) * 100, 1)
        } 
        for lang, size in top_3
    ]
    
    return {
        "trait": main_trait,
        "percent": round(main_percent), 
        "top_languages": top_languages
    }
