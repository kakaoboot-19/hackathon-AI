import boto3   # AWS SDK
from fastapi import UploadFile, HTTPException   # FastAPI 타입
import uuid
from datetime import datetime
import os

class S3Service:
    def __init__(self):
        # 환경변수에서 AWS 설정 읽기
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "ap-northeast-2")
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")
        
        # 환경변수가 모두 있으면 S3 클라이언트 생성
        if self.aws_access_key and self.aws_secret_key and self.s3_bucket:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            print(f"S3 연결: {self.s3_bucket}")
        else:
            self.s3_client = None
    
    async def upload_image(self, file: UploadFile) -> dict:
        # 1. S3 클라이언트 체크
        if self.s3_client is None:
            raise HTTPException(500, "S3 설정 필요")
        
        # 2. 파일 타입 검증 (이미지만 허용)
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(400, "이미지 파일만 가능")
        
        # 3. 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = file.filename.split('.')[-1]
        file_key = f"images/{timestamp}_{unique_id}.{extension}"
        
        try:
            # 4. S3에 업로드
            self.s3_client.upload_fileobj(
                file.file,          # 파일 스트림 (바이너리 데이터)
                self.s3_bucket,
                file_key,           # S3 내부 경로
                ExtraArgs={
                    'ContentType': file.content_type,   # MIME 타입 설정
                }
            )
            
            # 5. 업로드된 파일의 공개 URL 생성
            # 형식: https://버킷명.s3.리전.amazonaws.com/파일경로
            image_url = f"https://{self.s3_bucket}.s3.{self.aws_region}.amazonaws.com/{file_key}"
            
            return {
                "success": True,
                "image_url": image_url, # 브라우저에서 접근 가능한 URL
                "file_key": file_key
            }
        except Exception as e:
            raise HTTPException(500, f"업로드 실패: {str(e)}")

s3_service = S3Service()