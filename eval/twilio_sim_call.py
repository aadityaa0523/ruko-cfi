"""Keypad-phone line, end to end with a Twilio-protocol simulator (NOT a real phone call).

Plays the scripted Hinglish scam call (synthetic Gnani voices) into /twilio/stream exactly as Twilio Media Streams
would: 8 kHz G.711 mu-law, 20 ms frames, in real time. Checks that Ruko speaks a warning *into the call* and that
the 1930 report appears at /api/calls.
Run with the server up and GNANI_API_KEY set:  python -m eval.twilio_sim_call [http://host:port] [call.wav]
"""
import asyncio, audioop, base64, json, re, sys, time, wave
from pathlib import Path
import httpx, websockets


async def main(base="http://localhost:8870", wav_path=r"C:\Users\Aadityaa\iqoo\ruko\video_build\call2.wav"):
    with wave.open(wav_path) as w:
        pcm, rate = w.readframes(w.getnframes()), w.getframerate()
    pcm8, _ = audioop.ratecv(pcm, 2, 1, rate, 8000, None)
    ulaw = audioop.lin2ulaw(pcm8, 2)[: 8000 * 34]          # the first 34 s: the whole scam, then hang up
    async with httpx.AsyncClient(timeout=60) as c:
        twiml = (await c.post(f"{base}/twilio/voice?lang=hi-en&family=simfamily2611", data={"CallSid": "CA-sim"})).text
    token = re.search(r'name="token" value="([^"]+)"', twiml).group(1)
    ws_url = re.search(r'Stream url="([^"]+)"', twiml).group(1)
    ws_url = base.replace("http", "ws", 1) + "/twilio/stream" if "localhost" in base else ws_url
    out, t0 = [], time.monotonic()
    async with websockets.connect(ws_url, max_size=None) as ws:
        await ws.send(json.dumps({"event": "connected"}))
        await ws.send(json.dumps({"event": "start", "streamSid": "MZ-sim", "start": {"callSid": "CA-sim",
                                  "customParameters": {"token": token, "lang": "hi-en", "family": "simfamily2611"}}}))

        async def reader():
            try:
                async for raw in ws:
                    m = json.loads(raw)
                    if m.get("event") == "media":
                        out.append((round(time.monotonic() - t0, 1), len(base64.b64decode(m["media"]["payload"]))))
            except websockets.ConnectionClosed:
                pass
        rt = asyncio.create_task(reader())
        start = time.monotonic()
        for k, i in enumerate(range(0, len(ulaw), 160)):
            await ws.send(json.dumps({"event": "media", "media": {"track": "inbound", "payload": base64.b64encode(ulaw[i:i + 160]).decode()}}))
            d = start + (k + 1) * 0.02 - time.monotonic()
            if d > 0:
                await asyncio.sleep(d)
        await ws.send(json.dumps({"event": "stop"}))
        await asyncio.sleep(6)
        rt.cancel()
    async with httpx.AsyncClient(timeout=60) as c:
        calls = (await c.get(f"{base}/api/calls?c=simfamily2611")).json()
        assert (await c.get(f"{base}/api/calls")).json() == [], "calls must not be listed without a family code"
    bursts, last = [], -9
    for t, n in out:                                         # group outbound audio into spoken messages
        if t - last > 1.5:
            bursts.append([t, 0])
        bursts[-1][1] += n; last = t
    print("audio Ruko spoke into the call (start s, seconds of audio):", [(t, round(n / 8000, 1)) for t, n in bursts])
    p = calls[0] if calls else {}
    print("report at /api/calls:", p.get("level"), p.get("score"), "| source", p.get("source"))
    assert len(bursts) >= 2 and p.get("level") in ("high", "critical"), "keypad line did not warn"
    print("OK: announced, warned inside the call, and filed the report")


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:]))
