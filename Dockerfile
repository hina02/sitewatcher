# ==========================================
# Builder Stage: 依存関係のインストール
# ==========================================
FROM python:3.12-slim-bookworm AS builder
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# ==========================================
# Runtime Stage: 実行用イメージ
# ==========================================
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

RUN useradd -m appuser
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
COPY ./app /app/app

CMD ["uvicorn", "app/main:app", "--host", "0.0.0.0", "--port", "8000"]