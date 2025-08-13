# syntax=docker/dockerfile:1.7-labs

# --- Pin the base image by digest (resolved at build time) ---
ARG PY_IMAGE=python:3.12-slim
ARG PY_DIGEST=sha256:REPLACE_ME   # workflow will inject the real digest
FROM ${PY_IMAGE}@${PY_DIGEST}

# Labels (OCI recommended set)
LABEL org.opencontainers.image.title="FiveOhOh"
LABEL org.opencontainers.image.description="An HTTP chaos server for testing client error handling, with random status codes, delays, malformed JSON, and connection drops."
LABEL org.opencontainers.image.url="https://github.com/cymylau/FiveOhOh"
LABEL org.opencontainers.image.source="https://github.com/cymylau/FiveOhOh"
LABEL org.opencontainers.image.documentation="https://github.com/cymylau/FiveOhOh#readme"
LABEL org.opencontainers.image.vendor="cymylau"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="cymylau <your-email@example.com>"
# Build-time metadata (populated by workflow)
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"
# Record the pinned base
LABEL org.opencontainers.image.base.name="${PY_IMAGE}"
LABEL org.opencontainers.image.base.digest="${PY_DIGEST}"

# App setup
WORKDIR /app
COPY fiveohoh.py .
RUN pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8000
CMD ["uvicorn", "fiveohoh:app", "--host", "0.0.0.0", "--port", "8000"]