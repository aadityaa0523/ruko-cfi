"""Ruko backend: the browser hears the call (Web Speech API) and sends each line of text here; the server scores
the call, tells the browser when to warn out loud, and on hang-up builds the golden-hour pack (evidence,
complaint, family alert). No audio ever reaches the server.

Run from the ruko/ folder:  .venv/Scripts/python -m uvicorn backend.app:app --port 8870
"""
import json
import mimetypes
import os
import time
from datetime import datetime
from pathlib import Path

from typing import Literal

from fastapi import FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import family as fam
from backend import langs
from backend.check import check_text
from backend.pack import build_pack
from backend.risk import CallRisk
from backend.scripts import SAFE, SCAM

ROOT = Path(__file__).resolve().parent.parent
mimetypes.add_type("application/manifest+json", ".webmanifest")
WAITLIST = ROOT / "data" / "waitlist.jsonl"
langs.load_env(ROOT / ".env")

app = FastAPI(title="Ruko")
MAX_SESSION_S = 1800
MAX_LINES = 600
app.include_router(fam.router)


@app.get("/api/health")
def health():
    return {"languages": list(langs.LANGS)}


@app.get("/api/scripts")
def scripts():
    return {"scam": SCAM, "safe": SAFE}


class Lines(BaseModel):
    lines: list[str]
    lang: str = "hi-en"


@app.post("/api/analyze")
def analyze(body: Lines):
    """Text test mode: score a call line by line without audio, and build its pack."""
    risk = CallRisk()
    states = [risk.feed(line) for line in body.lines]
    lines = [{"t": i * 4.0, "text": t, "risk": s} for i, (t, s) in enumerate(zip(body.lines, states))]
    return {"states": states, "pack": build_pack(lines, datetime.now(), body.lang if langs.valid_lang(body.lang) else "hi-en")}


class Lead(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    contact: str = Field(min_length=3, max_length=100)
    role: Literal["family", "self", "bank", "telco", "police", "other"]
    consent: Literal[True]


@app.post("/api/waitlist")
def waitlist(lead: Lead):
    """Pilot sign-ups. shortcut: a JSONL file on local disk, move to a database before relying on it in production."""
    WAITLIST.parent.mkdir(exist_ok=True)
    with WAITLIST.open("a", encoding="utf-8") as f:
        f.write(json.dumps({**lead.model_dump(), "at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False) + "\n")
    return {"ok": True}


class ScoreRequest(BaseModel):
    lines: list[str] = Field(min_length=1, max_length=200)


@app.post("/v1/score")
def score(body: ScoreRequest, x_ruko_key: str = Header("")):
    """Partner API: score a call's transcript lines for scam steps. Key "demo" is public and capped at 20 lines."""
    keys = {k.strip() for k in os.environ.get("RUKO_PARTNER_KEYS", "").split(",") if k.strip()}
    if x_ruko_key not in keys and not (x_ruko_key == "demo" and len(body.lines) <= 20):
        return JSONResponse({"error": "missing or invalid X-Ruko-Key"}, status_code=401)
    risk = CallRisk()
    for line in body.lines:
        state = risk.feed(line[:2000])
    return {k: state[k] for k in ("level", "score", "flags", "playbook")}


class CheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@app.post("/api/check")
def check(body: CheckRequest):
    """Check a message, link, UPI request or number (no audio, nothing stored)."""
    return check_text(body.text)


def warning_msg(lang: str, state: dict) -> dict:
    """The browser speaks the warning itself, in its own voice for this language."""
    return {"type": "warning", "text": langs.LANGS[lang]["warning"], "say": langs.say_text(lang),
            "bcp": langs.LANGS["hi-IN" if lang == "hi-en" else lang]["bcp"], "level": state["level"]}


@app.get("/api/warning")
def warning(lang: str = "hi-en"):
    """The warning text for one language, so the settings screen can play it once."""
    if not langs.valid_lang(lang):
        return JSONResponse({"error": "unknown lang"}, status_code=400)
    return warning_msg(lang, {"level": "test"})


@app.websocket("/ws/listen")
async def listen(ws: WebSocket, lang: str = "hi-en", family: str = ""):
    """Browser sends {"type": "line", "text": ...} for each finished sentence it heard, then {"type": "hangup"}."""
    await ws.accept()
    if not langs.valid_lang(lang):
        await ws.close(code=1008, reason="bad lang")
        return
    code = family or None
    risk = CallRisk()
    await fam.publish(code, {"type": "call_start", "at": datetime.now().isoformat(timespec="seconds")})
    started, t0 = datetime.now(), time.monotonic()
    lines: list[dict] = []
    await ws.send_json({"type": "connected"})
    try:
        while time.monotonic() - t0 < MAX_SESSION_S:
            m = await ws.receive_json()
            if m.get("type") == "hangup":
                pack = build_pack(lines, started, lang)
                await ws.send_json({"type": "pack", **pack})
                await fam.publish(code, {"type": "pack", **pack})
                await ws.close()
                return
            text = str(m.get("text", "")).strip()[:2000] if m.get("type") == "line" else ""
            if not text or len(lines) >= MAX_LINES:
                continue
            state = risk.feed(text)
            lines.append({"t": round(time.monotonic() - t0, 1), "text": text, "risk": state})
            msg = {"type": "transcript", "text": text, "risk": state}
            await ws.send_json(msg)
            await fam.publish(code, msg)
            if state["alert"]:
                warn = warning_msg(lang, state)
                await ws.send_json(warn)
                await fam.publish(code, warn)
        await _safe_send(ws, {"type": "error", "message": "Session limit of 30 minutes reached."})
    except (WebSocketDisconnect, ValueError):
        pass  # browser gone or sent something that is not JSON
    finally:
        await fam.publish(code, {"type": "call_end"})


async def _safe_send(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass  # browser already gone


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
