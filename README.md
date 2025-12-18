# hackathon-AI# GitBTI Backend API

GitHub 기반 개발자 성향 분석 API

## 📁 프로젝트 구조

```
gitbti-backend/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
│
└── app/
    ├── main.py              # FastAPI 앱
    ├── config.py            # 환경변수
    │
    ├── api/
    │   └── __init__.py      # POST /api/gitbti
    │
    ├── services/
    │   ├── github_service.py
    │   └── s3_service.py
    │
    └── ai/                  # AI 팀 작업
        ├── queries.py
        ├── analyzer.py
        └── image_generator.py
```

## 🚀 로컬 개발

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일에 토큰 입력

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 서버 실행
uvicorn app.main:app --reload --port 8000

# 4. API 테스트
curl -X POST http://localhost:8000/api/gitbti \
  -H "Content-Type: application/json" \
  -d '{"username": "torvalds"}'
```

## 🐳 Docker 배포

```bash
# docker-compose.yml에 환경변수 설정 후
docker-compose up -d
```

## 📡 API 명세

### POST /api/gitbti

**Request:**
```json
{
  "username": "torvalds"
}
```

**Response:**
```json
{
  "role": {
    "type": "NBFI",
    "description": "밤의 폭발적인 문서화 개발자"
  },
  "image": {
    "url": "https://s3.../image.png",
    "description": "밤하늘 아래에서 코딩하는 개발자"
  },
  "stats": {
    "dayVsNight": 70,
    "steadyVsBurst": 80,
    "indieVsCrew": 60,
    "specialVsGeneral": 75
  }
}
```

## 🤖 AI 팀 통합

1. `app/ai/analyzer.py` - 분석 로직 작성
2. `app/ai/image_generator.py` - 이미지 생성 작성
3. 파일 교체 → 즉시 동작