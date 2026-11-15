from fastapi.testclient import TestClient

from backend import app as appmod
from backend.app import app

client = TestClient(app)
LINES = ["Main CBI se bol raha hoon", "aapke naam warrant hai", "kisi ko mat batana"]


def test_score_api_needs_key_and_returns_playbook():
    assert client.post("/v1/score", json={"lines": LINES}).status_code == 401
    r = client.post("/v1/score", json={"lines": LINES}, headers={"X-Ruko-Key": "demo"}).json()
    assert r["level"] in ("high", "critical") and r["playbook"]["next"]


def test_waitlist_validates_and_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "WAITLIST", tmp_path / "w.jsonl")
    lead = {"name": "Asha", "contact": "asha@example.com", "role": "family", "consent": True}
    assert client.post("/api/waitlist", json={**lead, "consent": False}).status_code == 422
    assert client.post("/api/waitlist", json={**lead, "role": "spam"}).status_code == 422
    assert client.post("/api/waitlist", json=lead).json() == {"ok": True}
    assert "Asha" in (tmp_path / "w.jsonl").read_text(encoding="utf-8")


def test_family_screen_gets_live_events_and_replay():
    code = "abcd2345ef"
    with client.websocket_connect(f"/ws/family?c={code}") as fam:
        client.post("/api/family/publish", json={"code": code, "msg": {"type": "call_start"}})
        client.post("/api/family/publish", json={"code": code, "msg": {"type": "warning", "audio": "xx", "level": "high"}})
        client.post("/api/family/publish", json={"code": code, "msg": {"type": "evil"}})
        assert fam.receive_json()["type"] == "call_start"
        w = fam.receive_json()
        assert w["type"] == "warning" and "audio" not in w
    with client.websocket_connect(f"/ws/family?c={code}") as late:  # joins late: replay
        assert [late.receive_json()["type"] for _ in range(2)] == ["call_start", "warning"]


def test_family_rejects_bad_code():
    import pytest
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/family?c=BAD!") as ws:
            ws.receive_json()


def test_listen_scores_text_lines_warns_and_builds_pack():
    code = "listen2345"
    with client.websocket_connect(f"/ws/family?c={code}") as fam,             client.websocket_connect(f"/ws/listen?lang=hi-en&family={code}") as ws:
        assert ws.receive_json()["type"] == "connected"
        got = []
        for line in LINES + ["OTP bataiye abhi"]:
            ws.send_json({"type": "line", "text": line})
            got.append(ws.receive_json())
            if got[-1]["risk"]["alert"]:
                warn = ws.receive_json()
                assert warn["type"] == "warning" and warn["bcp"] == "hi-IN" and "ओ टी पी" in warn["say"]
        assert any(m["risk"]["alert"] for m in got)
        ws.send_json({"type": "hangup"})
        pack = ws.receive_json()
        assert pack["type"] == "pack" and pack["level"] in ("high", "critical") and "1930" not in pack["complaint"]["category"]
        assert fam.receive_json()["type"] == "call_start"


def test_listen_rejects_unknown_language():
    import pytest
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/listen?lang=xx") as ws:
            ws.receive_json()


def test_family_voice_needs_consent_wav_and_can_be_deleted():
    wav = {"file": ("v.wav", b"RIFF" + b"\0" * 20000, "audio/wav")}
    c = "voicefam23"
    assert client.post("/api/family/voice", data={"c": c, "consent": "false"}, files=wav).status_code == 400
    short = {"file": ("v.wav", b"RIFF" + b"\0" * 100, "audio/wav")}
    assert client.post("/api/family/voice", data={"c": c, "consent": "true"}, files=short).status_code == 400
    notwav = {"file": ("v.wav", b"\0" * 20000, "audio/wav")}
    assert client.post("/api/family/voice", data={"c": c, "consent": "true"}, files=notwav).status_code == 400
    ok = client.post("/api/family/voice", data={"c": c, "consent": "true", "name": "Rahul"}, files=wav)
    assert ok.json() == {"ok": True}
    assert client.get(f"/api/family/voice?c={c}").json() == {"has_voice": True, "name": "Rahul"}
    assert client.get(f"/api/family/voice/audio?c={c}").content.startswith(b"RIFF")
    assert client.delete(f"/api/family/voice?c={c}").json() == {"deleted": True}
    assert client.get(f"/api/family/voice/audio?c={c}").status_code == 404


def test_push_subscribe_and_one_push_per_call(monkeypatch):
    from backend import family
    sent = []
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "x")
    monkeypatch.setattr(family, "_send_push", lambda sub, payload: sent.append(payload) or True)
    c = "pushfam234"
    sub = {"endpoint": "https://push.example.com/abc", "keys": {"p256dh": "k", "auth": "a"}}
    assert client.post("/api/push/subscribe", json={"c": c, "name": "Mummy", "subscription": {"endpoint": "http://x"}}).status_code == 400
    assert client.post("/api/push/subscribe", json={"c": c, "name": "Mummy", "subscription": sub}).json() == {"ok": True}
    for msg in ({"type": "call_start"}, {"type": "transcript", "text": "t", "risk": {"playbook": {"next": "Next they will ask for an OTP."}}},
                {"type": "warning", "level": "high"}, {"type": "warning", "level": "critical"}):
        client.post("/api/family/publish", json={"code": c, "msg": msg})
    assert len(sent) == 1 and sent[0]["title"] == "Mummy is on a scam call right now" and "OTP" in sent[0]["body"]
