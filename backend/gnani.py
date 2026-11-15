"""Optional speech engine: Gnani Vachana Prisma STT (realtime WS) and Timbre TTS (REST).

Used only when GNANI_API_KEY is set; without it Ruko uses the browser's own speech recognition and voice."""
import asyncio
import os
import re
from pathlib import Path

import httpx

STT_WS = "wss://api.vachana.ai/stt/v3/stream"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

# Scam vocabulary Prisma v3.0 should recognise reliably (keyterms, max 200).
KEYTERMS = [
    "OTP", "KYC", "CBI", "RBI", "UPI", "UPI PIN", "CVV", "AnyDesk", "TeamViewer", "QuickSupport",
    "PM Kisan", "Ayushman", "digital arrest", "warrant", "FIR", "QR code", "screen share",
    "customs", "narcotics", "cyber cell", "crime branch", "safe account", "1930",
]

# UI language -> Prisma language, Timbre v2.5 language/voice, spoken warning (numbers in spoken form).
LANGS = {
    "hi-en": {"stt": "hi-IN", "tts": "hi-en", "voice": "Poorvi", "v3": "hi-IN",
              "warning": "Ruko! Yeh call dhokha lag rahi hai. Bank, police ya sarkar kabhi phone par O T P "
                         "ya paise nahi maangte. Phone kaat dijiye, aur ek nau teen shunya par call kijiye."},
    "hi-IN": {"stt": "hi-IN", "tts": "hi-IN", "voice": "Nalini", "v3": "hi-IN",
              "warning": "रुकिए! यह कॉल धोखा लग रही है। बैंक, पुलिस या सरकार कभी फ़ोन पर ओ टी पी या पैसे नहीं "
                         "माँगते। फ़ोन काट दीजिए, और एक नौ तीन शून्य पर कॉल कीजिए।"},
    "kn-IN": {"stt": "kn-IN", "tts": "kn-IN", "voice": "Saanvi", "v3": "kn-IN",
              "warning": "ನಿಲ್ಲಿ! ಇದು ವಂಚನೆಯ ಕರೆ ಅಂತ ಅನಿಸುತ್ತಿದೆ. ಬ್ಯಾಂಕ್, ಪೊಲೀಸ್ ಅಥವಾ ಸರ್ಕಾರ ಯಾವತ್ತೂ ಫೋನಿನಲ್ಲಿ ಒ ಟಿ ಪಿ ಅಥವಾ ಹಣ "
                         "ಕೇಳುವುದಿಲ್ಲ. ಕರೆ ಕಟ್ ಮಾಡಿ, ಒಂದು ಒಂಬತ್ತು ಮೂರು ಸೊನ್ನೆಗೆ ಕರೆ ಮಾಡಿ."},
    "te-IN": {"stt": "te-IN", "tts": "te-IN", "voice": "Suhana", "v3": "te-IN",
              "warning": "ఆగండి! ఇది మోసపు కాల్ లాగా ఉంది. బ్యాంక్, పోలీసులు లేదా ప్రభుత్వం ఎప్పుడూ ఫోన్‌లో ఓ టి పి లేదా డబ్బు "
                         "అడగరు. కాల్ కట్ చేసి, ఒకటి తొమ్మిది మూడు సున్నాకి కాల్ చేయండి."},
    "ta-IN": {"stt": "ta-IN", "tts": "ta-IN", "voice": "Asmita", "v3": "ta-IN",
              "warning": "நிறுத்துங்கள்! இது மோசடி அழைப்பு போல் தெரிகிறது. வங்கியோ, காவல்துறையோ, அரசாங்கமோ ஒருபோதும் "
                         "தொலைபேசியில் ஓ டி பி அல்லது பணம் கேட்காது. அழைப்பைத் துண்டித்து, ஒன்று ஒன்பது மூன்று "
                         "பூஜ்ஜியம் என்ற எண்ணை அழையுங்கள்."},
    # Marathi, Bengali, Gujarati, Malayalam: warning text drafted without a native review yet.
    "mr-IN": {"stt": "mr-IN", "tts": "mr-IN", "voice": "Zahira", "v3": "mr-IN",
              "warning": "थांबा! हा कॉल फसवणुकीचा वाटतो. बँक, पोलीस किंवा सरकार कधीही फोनवर ओ टी पी किंवा पैसे मागत नाहीत. "
                         "फोन कट करा, आणि एक नऊ तीन शून्य वर कॉल करा."},
    "bn-IN": {"stt": "bn-IN", "tts": "bn-IN", "voice": "Kirra", "v3": "bn-IN",
              "warning": "থামুন! এই কলটি প্রতারণা মনে হচ্ছে। ব্যাংক, পুলিশ বা সরকার কখনও ফোনে ও টি পি বা টাকা চায় না। "
                         "ফোন কেটে দিন, আর এক নয় তিন শূন্যে কল করুন।"},
    "gu-IN": {"stt": "gu-IN", "tts": "gu-IN", "voice": "Falak", "v3": "gu-IN",
              "warning": "રોકાઓ! આ કૉલ છેતરપિંડી લાગે છે. બેંક, પોલીસ કે સરકાર ક્યારેય ફોન પર ઓ ટી પી કે પૈસા માંગતી નથી. "
                         "ફોન કાપી નાખો, અને એક નવ ત્રણ શૂન્ય પર કૉલ કરો."},
    "ml-IN": {"stt": "ml-IN", "tts": "ml-IN", "voice": "Reshma", "v3": "ml-IN",
              "warning": "നിൽക്കൂ! ഈ കോൾ തട്ടിപ്പാണെന്ന് തോന്നുന്നു. ബാങ്കോ പോലീസോ സർക്കാരോ ഒരിക്കലും ഫോണിൽ ഒ ടി പി യോ പണമോ ചോദിക്കില്ല. "
                         "ഫോൺ കട്ട് ചെയ്യൂ, ഒന്ന് ഒമ്പത് മൂന്ന് പൂജ്യം എന്ന നമ്പറിൽ വിളിക്കൂ."},
    "en-IN": {"stt": "en-IN", "tts": "en-IN", "voice": "Kaveri", "v3": "en-IN",
              "warning": "Stop! This call looks like a scam. Banks, police and the government never ask for an "
                         "O T P or money on the phone. Hang up, and call one nine three zero."},
}


# "auto": Prisma identifies the language (indic-auto) and Ruko warns in the language it heard.
AUTO = "auto"
DETECTED = {"hi-IN": "hi-en", "kn-IN": "kn-IN", "te-IN": "te-IN", "ta-IN": "ta-IN", "en-IN": "en-IN",
            "mr-IN": "mr-IN", "bn-IN": "bn-IN", "gu-IN": "gu-IN", "ml-IN": "ml-IN"}


def valid_lang(lang: str) -> bool:
    return lang == AUTO or lang in LANGS


def speak_lang(lang: str, detected: str | None = None) -> str:
    """Concrete warning language. Auto falls back to Hinglish for languages Ruko has no warning in yet."""
    return lang if lang != AUTO else DETECTED.get(detected or "", "hi-en")


def stt_code(lang: str) -> str:
    return "indic-auto" if lang == AUTO else LANGS[lang]["stt"]


def load_env(path: Path) -> None:
    """Minimal .env loader so the key never has to be typed into code or chat."""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def api_key() -> str:
    return os.environ.get("GNANI_API_KEY", "")


def stt_headers(lang: str, model: str, rate: int = 16000) -> dict:
    h = {"x-api-key-id": api_key(), "model": model, "x-sample-rate": str(rate)}
    if model == "prisma-v3.0":
        # One locale or indic-auto; codemix keeps the English words that callers mix in.
        h["language_code"] = stt_code(lang)
        h["format"] = "codemix"
        h["keyterms"] = ",".join(KEYTERMS)
        h["topic"] = "Phone call that may be a bank, police or government impersonation scam"
    else:
        h["language_code"] = stt_code(lang)
        h["format"] = "verbatim"
    return h


def elder_text(text: str) -> str:
    """Timbre v3.0 tags for elders: every sentence drawn out (<slow>), a short silence (<pauses>) between them.
    A tag lasts until the next tag, so <slow> is repeated after each pause."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?।])\s+", text) if p.strip()]
    return " <pauses> ".join(f"<slow> {p}" for p in parts)


def _tts_body(text: str, lang: str, whisper: bool, telephony: bool, elder: bool, voice: dict | None) -> dict:
    cfg = LANGS[lang]
    if voice:  # a family member's cloned voice (vachana-vc-v1), only with their recorded consent
        body = {"text": text, "model": "vachana-vc-v1", "speaker_embedding": voice}
        # vachana-vc-v1 returns 500 for mu-law (tested), so phone audio is fetched as PCM and encoded here.
        body["audio_config"] = ({"sample_rate": 8000, "num_channels": 1, "sample_width": 2,
                                 "encoding": "linear_pcm", "container": "raw"}
                                if telephony else {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                                                   "encoding": "linear_pcm", "container": "wav"})
        return body
    if whisper:
        body = {"text": f"<whispers> {text}", "voice": "Shivani", "model": "timbre-v3.0", "language": cfg["v3"]}
    elif elder:
        body = {"text": elder_text(text), "voice": "Shivani", "model": "timbre-v3.0", "language": cfg["v3"]}
    else:
        body = {"text": text, "voice": cfg["voice"], "model": "timbre-v2.5", "language": cfg["tts"]}
    body["speed"] = 0.85  # slowest allowed, for elders (API rejects the documented "slow" string)
    if telephony:
        body["audio_config"] = {"sample_rate": 8000, "num_channels": 1, "sample_width": 1,
                                "encoding": "pcm_mulaw", "container": "raw"}
    else:
        body["audio_config"] = {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                                "encoding": "linear_pcm", "container": "wav"}
    return body


def _cache_key(text, lang, whisper, telephony, elder, voice):
    return (text, lang, whisper, telephony, elder, voice["embedding"][:64] if voice else None)


def _remember(key, audio: bytes):
    if len(_TTS_CACHE) >= 64:
        _TTS_CACHE.pop(next(iter(_TTS_CACHE)))
    _TTS_CACHE[key] = audio


async def tts(text: str, lang: str, whisper: bool = False, telephony: bool = False, elder: bool = False,
              voice: dict | None = None) -> bytes:
    """Speak text with Timbre. v2.5 by default (named in the challenge); v3.0 for <whispers> or elder mode;
    vachana-vc-v1 when a cloned family voice is given. telephony=True returns raw 8 kHz G.711 mu-law."""
    key = _cache_key(text, lang, whisper, telephony, elder, voice)
    if key in _TTS_CACHE:  # warnings repeat: save credits and ~1 s of delay
        return _TTS_CACHE[key]
    body = _tts_body(text, lang, whisper, telephony, elder, voice)
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(4):  # the account allows one active TTS request at a time: wait and retry on 429
            r = await client.post(TTS_URL, json=body, headers={"X-API-Key-ID": api_key()})
            if r.status_code != 429:
                break
            await asyncio.sleep(1.5 * (attempt + 1))
    if r.status_code != 200:
        raise RuntimeError(f"Timbre {r.status_code}: {r.text[:300]}")
    audio = r.content
    _remember(key, audio)
    return audio


_TTS_CACHE: dict[tuple, bytes] = {}
