"""FastAPI 애플리케이션"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router

app = FastAPI(
    title="GitBTI API",
    description="GitHub 기반 개발자 성향 분석 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션: 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router, prefix="/api")


@app.get("/")
def root():
    """루트"""
    return {
        "message": "GitBTI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """헬스 체크"""
    return {"status": "healthy"}