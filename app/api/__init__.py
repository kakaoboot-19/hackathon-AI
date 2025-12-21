"""API 라우터"""
import json
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.github_service import get_github_data
from app.services.s3_service import s3_service
from app.test.demo import analyze_and_generate
from app.test.demo import generate_image
from app.ai.analyzer import analyzer
from app.ai.prompt_generator import prompt_generator
from app.ai.team_report import generate_team_report

router = APIRouter()


# ===== Request/Response Models =====

class GitBTIRequest(BaseModel):
    """요청"""
    username: str = Field(..., description="GitHub 사용자 이름")


class RoleData(BaseModel):
    """역할 정보"""
    role_en: str = Field(..., description="GitHub 사용자 이름 영어")
    role_kr: str = Field(..., description="GitHub 사용자 이름 한글")
    type: str = Field(..., description="Git-BTI 타입 (예: NBFI)")
    description: str = Field(..., description="타입 설명")


class ImageData(BaseModel):
    """이미지 정보"""
    url: str = Field(..., description="S3 이미지 URL")
    description: str = Field(..., description="이미지 설명")


class StatsData(BaseModel):
    """통계 (0-100)"""
    dayVsNight: int = Field(..., ge=0, le=100, description="Day(0) vs Night(100)")
    steadyVsBurst: int = Field(..., ge=0, le=100, description="Steady(0) vs Burst(100)")
    indieVsCrew: int = Field(..., ge=0, le=100, description="Crew(0) vs indie(100)")
    specialVsGeneral: int = Field(..., ge=0, le=100, description="General(0) vs Specialist(100)")


class GitBTIResponse(BaseModel):
    """응답"""
    role: RoleData
    image: ImageData
    stats: StatsData


# ===== Batch Request/Response Models =====

class GitBTIBatchRequest(BaseModel):
    """배치 요청 (최대 6명)"""
    usernames: List[str] = Field(..., min_length=1, max_length=6, description="GitHub 사용자 이름 리스트 (1-6명)")


class UserGitBTIResult(BaseModel):
    """개별 사용자 Git-BTI 결과"""
    username: str = Field(..., description="GitHub 사용자 이름")
    role: RoleData
    image: ImageData
    stats: StatsData


class TeamReportData(BaseModel):
    """팀 리포트"""
    synergy: List[str] = Field(..., description="팀 시너지 평가 (문장 단위 리스트)")
    warning: List[str] = Field(..., description="팀 위험요소 평가 (문장 단위 리스트)")


class GitBTIBatchResponse(BaseModel):
    """배치 응답"""
    users: List[UserGitBTIResult] = Field(..., description="각 사용자의 Git-BTI 결과")
    team_report: Optional[TeamReportData] = Field(None, description="팀 리포트 (2명 이상일 때만)")


# ===== Helper Functions for Batch Processing =====

async def process_single_user(username: str) -> dict:
    """
    단일 사용자의 Git-BTI를 생성합니다 (병렬 처리용 헬퍼 함수).

    Args:
        username: GitHub 사용자 이름

    Returns:
        dict: 사용자의 Git-BTI 결과
    """
    try:
        print(f"🔄 [{username}] 처리 시작...")

        # 1. GitHub 데이터 수집 (동기 → 비동기)
        github_data = await asyncio.to_thread(get_github_data, username)

        # 2. Analyzer (동기 → 비동기)
        data_result = await asyncio.to_thread(analyzer, github_data)

        # 3. Prompt Generator (동기 → 비동기)
        prompt_result = await asyncio.to_thread(prompt_generator, data_result)

        # 4. 이미지 생성 (동기 → 비동기)
        ai_image = await asyncio.to_thread(generate_image, prompt_result['image_prompt_content'])

        # 5. S3 업로드 (이미 async)
        s3_result = await s3_service.upload_pil_image(
            pil_image=ai_image,
            image_format="PNG"
        )

        print(f"✅ [{username}] 완료! 타입: {prompt_result['type']}")

        return {
            "username": username,
            "type": prompt_result["type"],
            "role_en": prompt_result["role_en"],
            "role_kr": prompt_result["role_kr"],
            "description": prompt_result["description"],
            "image_url": s3_result["image_url"],
            "stats": prompt_result["stats"]
        }

    except Exception as e:
        print(f"❌ [{username}] 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[{username}] 처리 실패: {str(e)}")


# ===== Batch API Endpoint =====

@router.post("/gitbti/batch", response_model=GitBTIBatchResponse)
async def create_gitbti_batch(req: GitBTIBatchRequest):
    """
    여러 사용자의 Git-BTI를 병렬로 생성합니다 (최대 6명).

    1. 모든 사용자를 병렬로 처리 (asyncio.gather)
    2. 2명 이상일 경우 팀 리포트 생성
    3. 결과 반환
    """
    try:
        # 배치 요청 검증
        if not req.usernames:
            raise HTTPException(status_code=400, detail="Username list cannot be empty")

        # 중복 제거
        unique_usernames = list(dict.fromkeys(req.usernames))  # 순서 유지하면서 중복 제거

        if len(unique_usernames) != len(req.usernames):
            print(f"⚠️  중복된 사용자명 제거: {len(req.usernames)}명 → {len(unique_usernames)}명")

        # 각 username 기본 검증
        for username in unique_usernames:
            if not username or not isinstance(username, str) or not username.strip():
                raise HTTPException(status_code=400, detail=f"Invalid username: {username}")

        print(f"\n{'='*60}")
        print(f"📦 배치 처리 시작: {len(unique_usernames)}명")
        print(f"   사용자: {', '.join(unique_usernames)}")
        print(f"{'='*60}\n")

        # 1. 모든 사용자를 병렬로 처리
        results = await asyncio.gather(
            *[process_single_user(username.strip()) for username in unique_usernames],
            return_exceptions=False  # 에러 발생 시 즉시 중단
        )

        # 2. 응답 형식으로 변환
        user_results = [
            UserGitBTIResult(
                username=result["username"],
                role=RoleData(
                    role_en=result["role_en"],
                    role_kr=result["role_kr"],
                    type=result["type"],
                    description=result["description"]
                ),
                image=ImageData(
                    url=result["image_url"],
                    description="Git-BTI 캐릭터 이미지"
                ),
                stats=StatsData(
                    dayVsNight=result["stats"]["dayVsNight"],
                    steadyVsBurst=result["stats"]["steadyVsBurst"],
                    indieVsCrew=result["stats"]["indieVsCrew"],
                    specialVsGeneral=result["stats"]["specialVsGeneral"]
                )
            )
            for result in results
        ]

        # 3. 팀 리포트 생성 (2명 이상일 때만)
        team_report = None
        if len(results) >= 2:
            print(f"\n🤝 팀 리포트 생성 중...")
            # username과 type만 추출
            team_data = [
                {"username": r["username"], "type": r["type"]}
                for r in results
            ]
            team_report_data = await asyncio.to_thread(generate_team_report, team_data)

            # synergy와 warning을 .으로 split하여 리스트로 변환 (빈 문자열 제거)
            synergy_list = [s.strip() for s in team_report_data["synergy"].split(".") if s.strip()]
            warning_list = [s.strip() for s in team_report_data["warning"].split(".") if s.strip()]

            team_report = TeamReportData(
                synergy=synergy_list,
                warning=warning_list
            )
            print(f"✅ 팀 리포트 생성 완료!")

        print(f"\n{'='*60}")
        print(f"🎉 배치 처리 완료: {len(results)}명")
        print(f"{'='*60}\n")

        return GitBTIBatchResponse(
            users=user_results,
            team_report=team_report
        )

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ 배치 처리 실패: {str(e)}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=str(e))