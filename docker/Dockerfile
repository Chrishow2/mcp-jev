FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JEV_TRANSPORT=streamable-http \
    JEV_HOST=0.0.0.0 \
    JEV_PORT=8000 \
    JEV_HTTP_PATH=/mcp \
    JEV_STATELESS_HTTP=true

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "mcp_jev.server"]
