# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="FiveOhOh" \
      org.opencontainers.image.description="An HTTP chaos server for testing client error handling, with random status codes, delays, malformed JSON, and connection drops." \
      org.opencontainers.image.url="https://github.com/cymylau/FiveOhOh" \
      org.opencontainers.image.source="https://github.com/cymylau/FiveOhOh" \
      org.opencontainers.image.documentation="https://github.com/cymylau/FiveOhOh/blob/main/README.md" \
      org.opencontainers.image.vendor="cymylau" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="richjjoh" \

# ---- Runtime tweaks ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ---- Non-root user ----
RUN groupadd --gid 1000 fiveohoh \
 && useradd  --uid 1000 --gid fiveohoh --create-home --shell /usr/sbin/nologin fiveohoh

# ---- App setup ----
WORKDIR /app

# Install deps first (better layer caching)
# Tip: pin your versions inside requirements.txt
COPY --chown=fiveohoh:fiveohoh requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy app code with correct ownership
COPY --chown=fiveohoh:fiveohoh fiveohoh.py /app/fiveohoh.py

# Drop privileges
USER fiveohoh

EXPOSE 8000

# Lightweight healthcheck using Python (no curl/wget)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python - <<'PY' || exit 1
import sys,urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/", timeout=2) as r:
        sys.exit(0 if 200 <= r.status < 500 else 1)
except Exception:
    sys.exit(1)
PY

CMD ["uvicorn", "fiveohoh:app", "--host", "0.0.0.0", "--port", "8000"]
