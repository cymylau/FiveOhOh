FROM python:3.12-slim

# OCI recommended labels
LABEL org.opencontainers.image.title="FiveOhOh"
LABEL org.opencontainers.image.description="An HTTP chaos server for testing client error handling, with random status codes, delays, malformed JSON, and connection drops."
LABEL org.opencontainers.image.url="https://github.com/cymylau/FiveOhOh"
LABEL org.opencontainers.image.source="https://github.com/cymylau/FiveOhOh"
LABEL org.opencontainers.image.documentation="https://github.com/cymylau/FiveOhOh/blob/main/README.md"
LABEL org.opencontainers.image.vendor="cymylau"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="richjjoh"

# Create group, user and home directories
RUN groupadd --gid 1000 fiveohoh && useradd --uid 1000 -gid fiveohoh --create-home fiveohoh

# Install app
WORKDIR /app
COPY fiveohoh.py .
RUN pip install --no-cache-dir fastapi uvicorn pydantic

USER fiveohoh

EXPOSE 8000
CMD ["uvicorn", "fiveohoh:app", "--host", "0.0.0.0", "--port", "8000"]
