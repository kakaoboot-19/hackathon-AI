import boto3
from fastapi import UploadFile, HTTPException
import uuid
from datetime import datetime
import os
import io
from typing import Optional

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
            # S3 버킷 URL 생성
            self.s3_base_url = f"https://{self.s3_bucket}.s3.{self.aws_region}.amazonaws.com"
            print(f"S3 연결: {self.s3_bucket}")
            print(f"S3 Base URL: {self.s3_base_url}")
        else:
            self.s3_client = None
    
    async def upload_image(self, file: UploadFile) -> dict:
        """사용자가 업로드한 이미지 파일을 S3에 저장"""
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
            
            # 5. 업로드된 파일의 공개 URL 생성 (S3 Direct)
            image_url = f"{self.s3_base_url}/{file_key}"
            
            return {
                "success": True,
                "image_url": image_url, # 브라우저에서 접근 가능한 URL
                "file_key": file_key
            }
        except Exception as e:
            raise HTTPException(500, f"업로드 실패: {str(e)}")
    
    async def upload_pil_image(
        self, 
        pil_image, 
        image_format: str = "PNG"
    ) -> dict:
        """AI가 생성한 PIL Image를 S3에 저장"""
        # 1. S3 클라이언트 체크
        if self.s3_client is None:
            raise HTTPException(500, "S3 설정 필요")
        
        # 2. 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = image_format.lower()
        file_key = f"ai-generated/{timestamp}_{unique_id}.{extension}"
        
        # 3. PIL Image → BytesIO 변환 (S3는 파일 객체만 받기 때문)
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format=image_format)
        img_buffer.seek(0)  # 읽기 포인터를 맨 앞으로 이동
        
        # 4. Content-Type 결정
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'WEBP': 'image/webp'
        }
        content_type = content_type_map.get(image_format.upper(), 'image/png')
        
        try:
            # 5. S3에 업로드
            self.s3_client.upload_fileobj(
                img_buffer,         # BytesIO 객체 (파일처럼 동작)
                self.s3_bucket,
                file_key,           # S3 내부 경로
                ExtraArgs={
                    'ContentType': content_type,   # MIME 타입 설정
                }
            )
            
            # 6. 업로드된 파일의 공개 URL 생성 (S3 Direct)
            image_url = f"{self.s3_base_url}/{file_key}"
            
            return {
                "success": True,
                "image_url": image_url, # 브라우저에서 접근 가능한 URL
                "file_key": file_key
            }
        except Exception as e:
            raise HTTPException(500, f"업로드 실패: {str(e)}")


s3_service = S3Service()