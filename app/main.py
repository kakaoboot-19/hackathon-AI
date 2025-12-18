from dotenv import load_dotenv # .env 파일을 환경변수로 로드 (로컬 개발용)
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from app.services import s3_service

app = FastAPI(title="Git.. ")

@app.get("/health")
async def health():
    return {"status": "healthy"}

# 이미지 업로드 API
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return await s3_service.upload_image(file)