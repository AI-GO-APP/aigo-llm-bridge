# 基底映像走 public.ecr.aws:平台建置機直拉 Docker Hub 容易被限流(429)
FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
COPY bridge ./bridge
# 平台注入 $PORT;一定要綁 0.0.0.0
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
