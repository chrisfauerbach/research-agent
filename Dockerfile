FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project metadata and install deps (cached layer)
COPY pyproject.toml README.md ./
RUN mkdir -p research_agent && touch research_agent/__init__.py \
    && uv pip install --system --no-cache -e ".[dev]"

# Copy full source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "research_agent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
