"""
S3 PIL Image 업로드 간단 테스트

실행:
1. pip install pillow boto3 --break-system-packages
2. .env 파일에 AWS 설정 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME)
3. python test_pil_upload.py
"""

from dotenv import load_dotenv
load_dotenv()

from PIL import Image, ImageDraw
import asyncio

# S3 서비스 임포트
import sys
sys.path.append('.')
from s3_service import s3_service


async def test_upload():
    print("🎨 1. PIL Image 생성 중...")
    
    # AI 모델이 이미지 생성했다고 가정
    # (실제로는: ai_image = stable_diffusion.generate(prompt))
    ai_image = Image.new('RGB', (512, 512), color='#667eea')
    draw = ImageDraw.Draw(ai_image)
    draw.text((200, 250), "Test Image", fill='white')
    
    print("✅ PIL Image 생성 완료")
    print(f"   타입: {type(ai_image)}")
    print(f"   크기: {ai_image.size}")
    
    print("\n📤 2. S3 업로드 중...")
    
    # S3에 업로드 (이게 전부!)
    result = await s3_service.upload_pil_image(
        pil_image=ai_image,
        image_format="PNG"
    )
    
    print("✅ S3 업로드 완료!")
    print(f"   URL: {result['image_url']}")
    print(f"   Key: {result['file_key']}")
    
    return result


if __name__ == "__main__":
    # 실행
    result = asyncio.run(test_upload())
    
    print("\n" + "="*60)
    print("🎉 테스트 성공! 브라우저에서 확인:")
    print(result['image_url'])
    print("="*60)