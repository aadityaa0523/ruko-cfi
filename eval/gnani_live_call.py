"""Run with the server up and GNANI_API_KEY in .env:  python -m eval.gnani_live_call
End-to-end check of /ws/hear: Gnani speaks a scam call, it is streamed like a mic, Ruko must warn and build a pack."""
import asyncio, audioop, io, json, sys, time, wave
from pathlib import Path
sys.path.insert(0, r"C:\Users\Aadityaa\iqoo\ruko-cfi")
import websockets
from backend import gnani

gnani.load_env(Path(r"C:\Users\Aadityaa\iqoo\ruko-cfi\.env"))
LINES = ["Namaste, main CBI se inspector Sharma bol raha hoon.", "Aapke naam par warrant nikla hai, aapko digital arrest kiya ja raha hai.",
         "Yeh baat kisi ko mat batana, aur phone mat kaatna.", "Abhi apne account ka OTP bataiye, verification ke liye."]


async def pcm16k(text):
    wav = await gnani.tts(text, "hi-en")
    with wave.open(io.BytesIO(wav)) as w:
        raw, rate, width = w.readframes(w.getnframes()), w.getframerate(), w.getsampwidth()
    pcm, _ = audioop.ratecv(raw, width, 1, rate, 16000, None)
    return pcm + b"\0" * 16000 * 2  # 1 s of silence after each sentence


async def main():
    clips = [await pcm16k(t) for t in LINES]
    t0 = time.monotonic(); got = []
    async with websockets.connect("ws://localhost:8870/ws/hear?lang=hi-en", max_size=None) as ws:
        async def reader():
            async for raw in ws:
                m = json.loads(raw); got.append(m)
                extra = m.get("text") or m.get("level") or ""
                print(f"{time.monotonic()-t0:5.1f}s {m['type']:10} {str(extra)[:70]!r}"
                      + (f" audio={len(m['audio'])}" if m.get("audio") else "") + (f" risk={m['risk']['level']}" if m.get("risk") else ""))
        rt = asyncio.create_task(reader())
        for pcm in clips:
            for i in range(0, len(pcm), 1024):
                await ws.send(pcm[i:i + 1024]); await asyncio.sleep(0.032)  # real time
        await ws.send(json.dumps({"type": "hangup"}))
        try:
            await asyncio.wait_for(rt, 20)
        except (asyncio.TimeoutError, websockets.ConnectionClosed):
            pass
    kinds = [m["type"] for m in got]
    assert "warning" in kinds and "pack" in kinds, kinds
    w = next(m for m in got if m["type"] == "warning")
    assert w.get("audio"), "warning has no Gnani audio"
    print("OK: warned with Gnani audio and built the pack; pack level", next(m for m in got if m["type"] == "pack")["level"])

asyncio.run(main())
