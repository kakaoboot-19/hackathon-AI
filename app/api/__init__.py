"""API 라우터"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.github_service import get_github_data
from app.services.s3_service import s3_service
from app.test.demo import analyze_and_generate
from app.test.demo import generate_image
from app.ai.analyzer import analyzer
from app.ai.prompt_generator import prompt_generator

router = APIRouter()


# ===== Request/Response Models =====

class GitBTIRequest(BaseModel):
    """요청"""
    username: str = Field(..., description="GitHub 사용자 이름")


class RoleData(BaseModel):
    """역할 정보"""
    role: str = Field(..., description="GitHub 사용자 이름")
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
    2. AI 분석 + 이미지 생성 (demo.py)
    3. S3 업로드
    4. 결과 반환 (프론트 형식)
    """
    try:
        # 1. GitHub 데이터 수집
        print(f"1️⃣ GitHub 데이터 수집 중: {req.username}")
        github_data = get_github_data(req.username)

        data_result = analyzer(github_data)
        prompt_result = prompt_generator(data_result)


        # DEBUG: GitHub 데이터 확인
        print("\n📦 GitHub 데이터 미리보기:")
        print(f"   - 사용자: {github_data['data']['user']['login']}")
        print(f"   - 이름: {github_data['data']['user'].get('name', 'N/A')}")
        print(f"   - 레포지토리 수: {len(github_data['data']['user']['repositories']['nodes'])}")
        if github_data['data']['user']['repositories']['nodes']:
            first_repo = github_data['data']['user']['repositories']['nodes'][0]
            print(f"   - 첫 번째 레포: {first_repo['name']}")
            print(f"   - 주 언어: {first_repo.get('primaryLanguage', {}).get('name', 'None')}")
        print()

        
        # 2. AI 분석 + 이미지 생성 (demo.py 로직)
        ai_image = generate_image(prompt_result['image_prompt'])
        print("2️⃣ AI 분석 및 이미지 생성 중...")
       
        # 3. S3 업로드
        print("3️⃣ S3 업로드 중...")
        s3_result = await s3_service.upload_pil_image(
            pil_image=ai_image,
            image_format="PNG"
        )

        print("✅ 완료!")
        print(f"   Git-BTI 타입: {prompt_result["type"]}")
        print(f"   이미지 URL: {s3_result['image_url']}")

        # 4. 프론트 형식으로 응답
        # percentage를 파싱해서 stats로 변환 (임시 - 나중에 수정 필요)
        # TODO: demo.py에서 percentage를 명확한 형식으로 리턴하도록 수정
        return GitBTIResponse(
            role=RoleData(
                role=prompt_result["role"],
                type=prompt_result["type"],
                description=prompt_result["description"]
            ),
            image=ImageData(
                url=s3_result["image_url"],
                description="Git-BTI 캐릭터 이미지"
            ),
            stats=StatsData(
                dayVsNight=50,  # TODO: percentage에서 파싱
                steadyVsBurst=50,
                indieVsCrew=50,
                specialVsGeneral=50
            )
        )

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))