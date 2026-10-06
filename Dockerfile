FROM python:3.13-slim

# 基础镜像已自带 tzdata，只需指定时区，日志时间戳即为本地时间
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 先装依赖，改业务代码时可复用这层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py logging_setup.py .

# logs 目录要在切非 root 用户前建好并授权，否则挂载卷写不进去
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# slim 镜像没有 curl，用 python 自检
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
