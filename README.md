# FiveOhOh - HTTP Chaos Server

**FiveOhOh** is a deliberately unreliable HTTP API designed to help you test client error handling.  
It randomly returns different HTTP status codes, introduces artificial delays, occasionally sends malformed JSON, and can simulate dropped connections.

This makes it ideal for:
- Testing how your code handles non-200 responses.
- Validating retry logic and backoff strategies.
- Chaos testing and resilience validation for HTTP clients.

---

## Features

- **Random HTTP status codes** — fully configurable via environment variables.
- **Random response delays** — simulate slow network or overloaded servers.
- **Malformed JSON** — test your parser's robustness.
- **Dropped connections** — simulate abrupt server terminations.
- **Configurable chaos** — tweak probabilities without changing code.

---

## Quick Start

Run the container with Docker:

```bash
docker run --rm -p 8000:8000 \
   -e CODES="200:0.7,429:0.1,500:0.1,503:0.1" \
   -e MAX_DELAY=3.0   -e MALFORMED_CHANCE=0.05 \
   -e DROP_CONN_CHANCE=0.02 \
   ghcr.io/cymylau/fiveohoh:latest
```
---

## Environment Variables

| Variable           | Default                                    | Description |
|--------------------|--------------------------------------------|-------------|
| `CODES`            | `200:0.7,429:0.1,500:0.1,503:0.1`           | Status code weights in `code:weight` format. Weights are relative, not strict probabilities. |
| `PAYLOAD`          | `{"status":"ok","service":"FiveOhOh"}`      | Base JSON payload for successful responses. |
| `MAX_DELAY`        | `3.0`                                       | Maximum artificial delay (seconds) before responding. |
| `MALFORMED_CHANCE` | `0.05`                                      | Chance of returning malformed JSON. |
| `DROP_CONN_CHANCE` | `0.02`                                      | Chance of simulating a dropped connection. |
| `LOG_REQUESTS`     | `true`                                      | Enable or disable simple request logging. |

---

## Endpoints

- `GET /healthz` — Always returns `{"ok": true, "service": "FiveOhOh"}`.
- `GET /data` — Returns success or error JSON, with chaos injected based on settings.
- `POST /data` — Same as `GET /data` but echoes back your request JSON on success.

---

## Example Usage

**Using `curl`:**

```bash
# Test the /healthz endpoint
curl -s http://localhost:8000/healthz | jq

# Test the /data endpoint multiple times to see different status codes
for i in {1..5}; do
  echo "Request $i:"
  curl -i http://localhost:8000/data
  echo
done

# POST some JSON data
curl -i -X POST http://localhost:8000/data   -H "Content-Type: application/json"   -d '{"name": "test-client"}'
```

**Using Python `requests`:**
```python
import requests

for i in range(5):
    r = requests.get("http://localhost:8000/data", timeout=5)
    print(i, r.status_code, r.text)
```

---

**Note:**  
`CODES` weights are **relative**. For example:
```
CODES="200:0.8,500:0.8,503:0.4"
```
produces a distribution of 40% 200, 40% 500, 20% 503.


**Don't trust me**

Clone this repo, review the code and build it yourself! 
