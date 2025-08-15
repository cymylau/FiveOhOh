"""
FiveOhOh - The HTTP Chaos Server
--------------------------------
A deliberately unreliable API for testing client error handling.

Features:
- Random HTTP status codes (weights treated as relative probabilities)
- Startup sanity log showing normalised probabilities
- Random response delays
- Optional malformed JSON
- Optional connection resets
"""

import json
import os
import random
import time
from typing import List, Tuple

from fastapi import FastAPI, Response, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# --- CONFIG HELPERS ---
def parse_codes(env: str, default: str) -> List[Tuple[int, float]]:
    """Parse 'code:weight,code:weight' -> [(code, weight), ...]."""
    raw = os.getenv(env, default)
    pairs: List[Tuple[int, float]] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            code_s, weight_s = part.split(":")
            code = int(code_s.strip())
            weight = float(weight_s.strip())
            pairs.append((code, weight))
        except Exception:
            print(f"[FiveOhOh][WARN] Could not parse code/weight entry: {part!r}")
    return pairs

def parse_float(env: str, default: float) -> float:
    try:
        return float(os.getenv(env, default))
    except ValueError:
        return default

def parse_bool(env: str, default: bool) -> bool:
    val = os.getenv(env)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y")

def validate_and_normalise(pairs: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
    """
    - Filter out invalid HTTP codes or non-positive weights.
    - Return list of (code, normalised_prob) where probs sum to 1 (if any valid).
    """
    valid: List[Tuple[int, float]] = []
    for code, w in pairs:
        if not (100 <= code <= 599):
            print(f"[FiveOhOh][WARN] Ignoring invalid HTTP code: {code}")
            continue
        if w <= 0:
            print(f"[FiveOhOh][WARN] Ignoring non-positive weight for {code}: {w}")
            continue
        valid.append((code, w))

    if not valid:
        # Fallback to sane defaults to avoid runtime errors
        print("[FiveOhOh][WARN] No valid codes provided; falling back to 200:1.0")
        return [(200, 1.0)]

    total = sum(w for _, w in valid)
    return [(code, w / total) for code, w in valid]

def log_distribution(raw_pairs: List[Tuple[int, float]], norm_pairs: List[Tuple[int, float]]) -> None:
    """Pretty-print the raw weights and normalised probabilities."""
    raw_total = sum(max(w, 0) for _, w in raw_pairs)  # ignore negatives in the sum
    print("\n[FiveOhOh] ---- Startup Status Code Distribution ----")
    print("[FiveOhOh] Raw weights (as provided):")
    for code, w in raw_pairs:
        print(f"[FiveOhOh]   {code}: weight={w}")
    print(f"[FiveOhOh] Sum of raw weights: {raw_total}")
    print("[FiveOhOh] Normalised probabilities (used by server):")
    for code, p in norm_pairs:
        pct = round(p * 100, 2)
        print(f"[FiveOhOh]   {code}: {pct}%")
    print("[FiveOhOh] ------------------------------------------------\n")

# --- CONFIGURATION (env-driven) ---
RAW_CODE_WEIGHTS = parse_codes("CODES", "200:0.7,429:0.1,500:0.1,503:0.1")
PAYLOAD = json.loads(os.getenv("PAYLOAD", '{"status":"ok","service":"FiveOhOh"}'))
MAX_DELAY = parse_float("MAX_DELAY", 3.0)         # seconds
MALFORMED_CHANCE = parse_float("MALFORMED_CHANCE", 0.05)  # 5% chance
DROP_CONN_CHANCE = parse_float("DROP_CONN_CHANCE", 0.02)   # 2% chance
LOG_REQUESTS = parse_bool("LOG_REQUESTS", True)

# Normalise and log at import time (container/app startup)
NORMALISED_CODE_PROBS = validate_and_normalise(RAW_CODE_WEIGHTS)
log_distribution(RAW_CODE_WEIGHTS, NORMALISED_CODE_PROBS)

# --- APP SETUP ---
app = FastAPI(title="FiveOhOh - HTTP Chaos Server")

@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    """Inject delays, optional connection drops, and basic logging."""
    if LOG_REQUESTS:
        print(f"[FiveOhOh] {request.method} {request.url.path}")

    # Simulate latency
    if MAX_DELAY > 0:
        delay = random.uniform(0, MAX_DELAY)
        if delay > 0.001:
            time.sleep(delay)

    # Simulate dropped connection (approximation via 500)
    if random.random() < DROP_CONN_CHANCE:
        return PlainTextResponse("Connection reset by chaos monkey.", status_code=500)

    return await call_next(request)

@app.get("/health")
def health():
    return {"ok": True, "service": "FiveOhOh"}

retryafter = 5  # starting value

@app.get("/429")
def fourtwonine():
    global retryafter
    if retryafter >= 0:
        retryafter -= 1
    
    if retryafter == -1:
        headers = {
        "X-FiveOhOh": "Chaos",
        "Cache-Control": "no-store",
        "X-Retry-After": str(0)
        }
        body = {"status": "OK"}
        return Response(
            content=json.dumps(body),
            media_type="application/json",
            status_code=200,
            headers=headers
        )
    else: 
        headers = {
         "X-FiveOhOh": "Chaos",
         "Cache-Control": "no-store",
          "X-Retry-After": str(retryafter)
        }
        body = {"status": "throttled", "retry_after": retryafter}
        return Response(
        content=json.dumps(body),
        media_type="application/json",
        status_code=429,
        headers=headers
    )

@app.get("/data")
def get_data():
    return _generate_response()

class EchoBody(BaseModel):
    anything: dict | list | str | int | float | bool | None = None

@app.post("/data")
def post_data(body: EchoBody):
    return _generate_response(extra={"received": body.model_dump()})

# --- RESPONSE GENERATOR ---
def _generate_response(extra: dict = None):
    """Return JSON or chaos depending on random draw."""
    codes, probs = zip(*NORMALISED_CODE_PROBS)
    status = random.choices(codes, weights=probs, k=1)[0]

    is_success = 200 <= status < 400
    payload = dict(PAYLOAD)
    if extra and is_success:
        payload.update(extra)

    # Chance of malformed JSON
    if random.random() < MALFORMED_CHANCE:
        bad_json = '{"status": "ok", "oops": '  # malformed JSON
        return Response(content=bad_json, media_type="application/json", status_code=status)

    body = payload if is_success else {"error": "simulated failure", "status": status}
    return Response(content=json.dumps(body), media_type="application/json", status_code=status)
