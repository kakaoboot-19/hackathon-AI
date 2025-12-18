"""API 라우터"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.github_service import get_github_data
from app.services.s3_service import upload_to_s3
from app.ai.analyzer import analyze_gitbti
from app.ai.image_generator import generate_image

router = APIRouter()


# ===== Request/Response Models =====

class GitBTIRequest(BaseModel):
    """요청"""
    username: str = Field(..., description="GitHub 사용자 이름")


class RoleData(BaseModel):
    """역할 정보"""
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


# ===== API Endpoint =====

@router.post("/gitbti", response_model=GitBTIResponse)
async def create_gitbti(req: GitBTIRequest):
    """
    Git-BTI 생성
    
    1. GitHub 데이터 수집
    2. AI 분석
    3. 이미지 생성
    4. S3 업로드
    5. 결과 반환 (프론트 형식)
    """
    try:
        # 1. GitHub 데이터 수집
        github_data = get_github_data(req.username)
        
        # 2. AI 분석
        gitbti_result = analyze_gitbti(github_data)
        
        # 3. 이미지 생성
        image_bytes = generate_image(gitbti_result)
        
        # 4. S3 업로드
        image_url = upload_to_s3(
            image_bytes=image_bytes,
            username=req.username,
            gitbti_type=gitbti_result["type"]
        )
        
        # 5. 프론트 형식으로 응답
        return GitBTIResponse(
            role=RoleData(
                type=gitbti_result["type"],
                description=gitbti_result["description"]
            ),
            image=ImageData(
                url=image_url,
                description=gitbti_result.get("image_description", "Git-BTI 캐릭터 이미지")
            ),
            stats=StatsData(
                dayVsNight=gitbti_result["stats"]["dayVsNight"],
                steadyVsBurst=gitbti_result["stats"]["steadyVsBurst"],
                indieVsCrew=gitbti_result["stats"]["indieVsCrew"],
                specialVsGeneral=gitbti_result["stats"]["specialVsGeneral"]
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))