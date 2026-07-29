# Runtime image for the onboarding agent API.
#
# Two-stage so the compiler toolchain that some wheels need doesn't ship in
# the final image. The embedding model is baked in at build time (see below)
# rather than downloaded on first request.

FROM python:3.12-slim AS builder

# Build-only: some wheels (psycopg, tokenizers) may compile from source when
# no manylinux wheel matches the platform.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install into a venv we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .


FROM python:3.12-slim AS runtime

# libgomp1 is required by torch (pulled in via sentence-transformers).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/opt/hf

# Bake the embedding model into the image. Without this the first request
# after every deploy pays a multi-hundred-MB download, and the container
# needs outbound internet at runtime — neither is acceptable for a demo on
# internal infrastructure.
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')" \
    && chmod -R a+rX /opt/hf

COPY main.py alembic.ini /app/
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY data/ /app/data/

RUN useradd --create-home --uid 10001 appuser

# init_db() writes its SQLite file to a RELATIVE path, i.e. into the working
# directory. Keep the code tree at /app root-owned and read-only, and run from
# a separate writable directory instead, so the app can create that file
# without any of its own source being writable at runtime.
# PYTHONPATH is what lets `main:app` still resolve from a different CWD.
ENV PYTHONPATH=/app
RUN mkdir -p /var/lib/onboard-agent && chown appuser:appuser /var/lib/onboard-agent
WORKDIR /var/lib/onboard-agent

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Single worker on purpose. The rate limiter keeps its counters in process
# memory, so N workers would allow N times the configured limit. Conversation
# state is in Postgres and is safe across workers; the limiter is not. Raise
# this only once the limiter uses shared state.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
