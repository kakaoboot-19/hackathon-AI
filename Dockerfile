# ========== Builder Stage ==========
FROM python:3.11-slim as builder

WORKDIR /code

COPY ./requirement.txt /code/requirement.txt

RUN pip install --no-cache-dir -r /code/requirement.txt


# ========== Runtime Stage ==========
FROM python:3.11-slim

WORKDIR /code

# 설치된 패키지만 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 앱 코드 복사
COPY ./app /code/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]