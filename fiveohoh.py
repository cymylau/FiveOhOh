import json
import os
import random
from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List, Tuple

app = FastAPI(title="Flaky Test Server")

def parse_codes(env: str, default: str) -> List[Tuple[int, float]]:
    """
    Parse "code:weight,code:weight" -> [(code, weight), ...]
    Example: "200:0.8,500:0.1,503:0.1"
    """
    raw = os.getenv(env, default)
    pairs = []
    for part in raw.split(","):
        code_s, weight_s = part.split(":")
        pairs.append((int(code_s.strip()), float(weight_s.strip())))
    return pairs

# Configure probabilities and JSON payload
CODE_WEIGHTS = parse_codes("CODES", "200:0.8,429:0.1,500:0.05,503:0.05")
PAYLOAD = json.loads(os.getenv("PAYLOAD", '{"status":"ok","service":"demo"}'))

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/data")
def get_data():
    codes, weights = zip(*CODE_WEIGHTS)
    status = random.choices(codes, weights=weights, k=1)[0]
    body = PAYLOAD if 200 <= status < 400 else {"error": "simulated failure", "status": status}
    return Response(content=json.dumps(body), media_type="application/json", status_code=status)

class EchoBody(BaseModel):
    anything: dict | list | str | int | float | bool | None = None

@app.post("/data")
def post_data(body: EchoBody):
    # Same random behavior for POSTs; echoes back input on success
    codes, weights = zip(*CODE_WEIGHTS)
    status = random.choices(codes, weights=weights, k=1)[0]
    resp = {"received": body.model_dump(), "status": "ok"} if 200 <= status < 400 else {"error": "simulated failure", "status": status}
    return Response(content=json.dumps(resp), media_type="application/json", status_code=status)