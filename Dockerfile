FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements/base.txt requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

EXPOSE 8000

ENV USE_POSTGRES=false

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/transacoes/?user_id=user-123')" || exit 1

CMD ["sh", "-c", "if [ \"$USE_POSTGRES\" = \"true\" ]; then python scripts/init_db.py; fi && exec uvicorn src.infrastructure.web.api.v1.api:app --host 0.0.0.0 --port 8000"]