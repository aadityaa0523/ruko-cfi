"""Live detection test through the real Gnani pipeline (/ws/hear), on synthetic calls.

For every scam and safe script in backend/scripts.py: speak each line with a Gnani voice, stream it in real time
exactly like a microphone (16 kHz PCM16, 1,024-byte frames), and record whether Ruko warned, after how many
sentences, and how soon after the sentence ended. Two conditions: clean, and "phone-band + noise" (squeezed to 8 kHz
and mixed with hiss), a rough stand-in for a speakerphone.

NOT measured here: a real phone on a real speaker in a real room, real accents, real callers. Synthetic voices only.

Run with the server up (GNANI_API_KEY in .env):  python -m eval.gnani_live_suite [http://host:port]
"""
import asyncio, audioop, io, json, random, sys, time, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import websockets
from backend import gnani
from backend.scripts import SAFE, SCAM

gnani.load_env(Path(__file__).resolve().parent.parent / ".env")
HERE = Path(__file__).parent
LANG = {"police_kannada": "kn-IN", "bank_telugu": "te-IN", "police_tamil": "ta-IN", "cyber_branch_english": "en-IN",
        "police_marathi": "mr-IN", "bank_bengali": "bn-IN", "police_gujarati": "gu-IN", "bank_malayalam": "ml-IN",
        "cbi_devanagari": "hi-IN", "tamil_family": "ta-IN", "marathi_family": "mr-IN", "bengali_family": "bn-IN",
        "card_bill_english": "en-IN"}
SILENCE_S = 1.2


TTS_LOCK = asyncio.Lock()  # Gnani allows one active TTS request at a time per account
WAVS: dict = {}


async def wav_for(text, lang):
    if (text, lang) not in WAVS:
        async with TTS_LOCK:
            WAVS[(text, lang)] = await gnani.tts(text, lang)
    return WAVS[(text, lang)]


async def clip(text, lang, noisy, rng):
    wav = await wav_for(text, lang)
    with wave.open(io.BytesIO(wav)) as w:
        raw, rate, width = w.readframes(w.getnframes()), w.getframerate(), w.getsampwidth()
    pcm, _ = audioop.ratecv(raw, width, 1, rate, 16000, None)
    if noisy:  # phone band, then hiss at roughly 5% of speech level
        low, _ = audioop.ratecv(pcm, 2, 1, 16000, 8000, None)
        pcm, _ = audioop.ratecv(low, 2, 1, 8000, 16000, None)
        rms = max(1, audioop.rms(pcm, 2))
        amp = int(rms * 0.05 * 1.7)
        hiss = b"".join(rng.randint(-amp, amp).to_bytes(2, "little", signed=True) for _ in range(len(pcm) // 2))
        pcm = audioop.add(pcm, hiss, 2)
    return pcm + b"\0" * int(16000 * 2 * SILENCE_S)


async def one(base, name, lines, scam, noisy, sem):
    lang = LANG.get(name, "hi-en")
    rng = random.Random(name)
    async with sem:
        clips = [await clip(t, lang, noisy, rng) for t in lines]
        bounds, acc = [], 0.0
        for c in clips:
            acc += len(c) / 32000
            bounds.append(acc)
        events = []
        async with websockets.connect(f"{base}/ws/hear?lang={lang}", max_size=None) as ws:
            t0 = time.monotonic()  # reset to the first audio frame below
            async def reader():
                async for raw in ws:
                    m = json.loads(raw)
                    if m["type"] in ("warning", "pack", "busy", "error"):
                        events.append((time.monotonic() - t0, m))
            rt = asyncio.create_task(reader())
            t0 = time.monotonic()
            # pace by the clock, not by sleep(0.032): Windows sleeps in ~16 ms steps, which made audio stream ~1.5x slow
            audio = b"".join(clips)
            start = time.monotonic()
            for k, i in enumerate(range(0, len(audio), 1024)):
                await ws.send(audio[i:i + 1024])
                delay = start + (k + 1) * 0.032 - time.monotonic()
                if delay > 0:
                    await asyncio.sleep(delay)
            stream_t0 = start
            await ws.send(json.dumps({"type": "hangup"}))
            try:
                await asyncio.wait_for(rt, 25)
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                pass
    warns = [t for t, m in events if m["type"] == "warning"]
    speech_end = acc - SILENCE_S  # end of the last spoken word
    pack = next((m for _, m in events if m["type"] == "pack"), {})
    err = next((m.get("message") or m["type"] for _, m in events if m["type"] in ("busy", "error")), None)
    first = warns[0] if warns else None
    sentence = next((i + 1 for i, b in enumerate(bounds) if first is not None and first <= b + 3), None) if first is not None else None
    return {"script": name, "lang": lang, "scam": scam, "noisy": noisy, "warned": bool(warns), "first_warning_s": round(first, 1) if first else None,
            "audio_s": round(acc, 1), "before_call_end": bool(first is not None and first <= speech_end), "after_sentence": sentence, "of_sentences": len(lines), "pack_level": pack.get("level"), "error": err}


async def main(base="http://localhost:8870"):
    base = base.replace("http", "ws", 1)
    sem = asyncio.Semaphore(1)  # Gnani allows one active request per account, so calls run one at a time
    for name, lines in {**SCAM, **SAFE}.items():  # speak every line first, so no TTS overlaps a live call
        for t in lines:
            await wav_for(t, LANG.get(name, "hi-en"))
    print("all lines spoken; streaming calls now", flush=True)
    jobs = [one(base, n, l, True, noisy, sem) for noisy in (False, True) for n, l in SCAM.items()] + \
           [one(base, n, l, False, noisy, sem) for noisy in (False, True) for n, l in SAFE.items()]
    res = []
    for fut in asyncio.as_completed(jobs):
        r = await fut; res.append(r)
        print(("SCAM" if r["scam"] else "SAFE"), "noisy" if r["noisy"] else "clean", r["script"], "warned" if r["warned"] else "-", r["first_warning_s"], r["error"] or "", flush=True)
    summary = {}
    for noisy in (False, True):
        sc = [r for r in res if r["scam"] and r["noisy"] == noisy and not r["error"]]
        sf = [r for r in res if not r["scam"] and r["noisy"] == noisy and not r["error"]]
        lat = sorted(r["first_warning_s"] - 0 for r in sc if r["warned"])
        summary["noisy" if noisy else "clean"] = {"scam_calls": len(sc), "caught": sum(r["warned"] for r in sc),
                                                   "warned_before_call_ended": sum(r["before_call_end"] for r in sc), "genuine_calls": len(sf),
                                                   "false_alarms": sum(r["warned"] for r in sf), "errors": sum(1 for r in res if r["noisy"] == noisy and r["error"])}
    out = {"measured": time.strftime("%Y-%m-%d"), "engine": "gnani prisma-v3.0 via /ws/hear", "summary": summary, "runs": sorted(res, key=lambda r: (r["noisy"], not r["scam"], r["script"]))}
    (HERE / "gnani_live_results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:]))
