<div align="center">

<img src="web/icon-192.png" width="88" alt="Ruko logo">

# Ruko

### Stop the scam, not just the number.

**A free, open-source scam-call guard for Indian families.** Ruko hears the call itself, spots the scammer's script mid-sentence, warns out loud in 10 Indian languages (even in a family member's own recorded voice), turns the family's phone red, and hands over the 1930 complaint.

No paid AI service, no speech API key: speech recognition and the spoken warning run in the user's own browser. MIT licensed, so any NGO, bank, telco or government body can run it.

![Licence](https://img.shields.io/badge/licence-MIT-informational?style=flat-square)
![Languages](https://img.shields.io/badge/languages-10_Indian-informational?style=flat-square)
![Tests](https://img.shields.io/badge/tests-83_passing-success?style=flat-square)
![Data](https://img.shields.io/badge/test_data-synthetic_only-lightgrey?style=flat-square)

Built for **Code for a Billion: Bharat Agentic-AI Hackathon 2026** (Code for India).

</div>

---

## The problem

In 2024, Indians lost **₹22,845 crore** to cyber fraud, **₹1,935 crore** of it to fake "digital arrest" calls, across **1.2 lakh complaints** (Ministry of Home Affairs, replies in Parliament). The people targeted are elders at home, farmers waiting for a PM-Kisan installment, and kirana owners living on UPI.

Caller ID checks the **number**, but scammers buy a new SIM every day. They never change the **script**:

> **Pose** "Main CBI officer bol raha hoon" → **Scare** "Aapke khilaf warrant nikla hai" → **Isolate** "Kisi ko mat batana" → **Ask** "OTP bataiye"

Ruko listens for that script.

## What Ruko does

| | Feature | How |
|---|---|---|
| 👂 | **Hears the call itself** on speakerphone, in the language you choose | The browser's Web Speech API (Chrome); only text reaches the server, never audio |
| 🧠 | **Tracks the 4-step scam script** and warns **before the next step** ("next they'll ask for your OTP") | Ruko's risk engine scores the whole call's pattern, not single keywords |
| 🗣️ | **Speaks the warning in 10 languages:** Hindi, Hinglish, Kannada, Telugu, Tamil, Marathi, Bengali, Gujarati, Malayalam, English. Slow for elders, or in a **family member's own recorded voice** | Browser speech synthesis; the family recording is real, never cloned |
| 👨‍👩‍👧 | **Family Shield:** the family's phone turns red live, with what was said and what to do; push alerts even when the page is closed | WebSockets + Web Push |
| 📝 | **After the call:** a ready 1930 / cybercrime.gov.in complaint, a one-tap number report, a ready report for DoT's **Chakshu** | Template-based, so it never invents facts |
| 🔎 | **Every day:** check any SMS, WhatsApp forward, link, UPI request or number; community **Scam Radar** | Rules + Supabase |
| 🤖 | **Android:** warns before you pick up, from community reports | `CallScreeningService` ([`android/`](android)) |
| 🏦 | **Scoring API:** banks and UPI apps score a live call before money moves | `POST /v1/score` |

## Why Ruko

| | **Ruko** | Truecaller | Airtel | Google Pixel |
|---|---|---|---|---|
| Understands what the caller says, live | ✅ | ❌ checks the number | ❌ checks call patterns | ✅ |
| Live warning language | ✅ **10 Indian, incl. Hinglish** | n/a | n/a | English only |
| Warns of the scammer's next move | ✅ | ❌ | ❌ | ❌ |
| Family sees the scam live | ✅ with what was said | Can block calls remotely | ❌ | ❌ |
| Free and open source | ✅ MIT | ❌ | ❌ | ❌ |
| After-call complaint + Chakshu | ✅ | ❌ | ❌ | ❌ |

<sub>Based on public announcements up to November 2026. Truecaller, Airtel, Google and Pixel are trademarks of their owners; Ruko is not affiliated with them. They're stronger at scale and at blocking known numbers; Ruko is built for the call they can't see: a new number with an old script.</sub>

## Proof, and what is not proven yet

| Test | Result |
|---|---|
| Scam engine on **real machine transcripts** of 14 scripted scam calls in 6 languages, recognition mistakes kept | **14/14 alarmed** |
| Same, on 8 genuine calls (bank reminders, delivery OTP, family) | **0/8 false alarms** |
| Message checker on 50 + 50 **held-out** messages (written blind, scored once) | **92% precision**, 72% recall |
| Live listening with browser speech recognition on a real speakerphone | **Not measured yet** |

All test data is synthetic. No real users yet. Method and limits: [docs/EVALUATION.md](docs/EVALUATION.md).

## How it works

```mermaid
flowchart LR
    A["📱 Call on speaker"] -->|mic| B["Browser speech recognition<br/>(Web Speech API)"]
    B -->|text only| C["Ruko risk engine<br/>pose → scare → isolate → ask"]
    C -->|alert| D["Warning in their language<br/>or a family member's recording"]
    C -->|live| E["👨‍👩‍👧 Family Shield<br/>phone turns red + push"]
    C -->|call ends| F["📝 1930 complaint pack"]
```

1. The guard page runs in Chrome on a second device (phones can't share the mic during a call). The browser turns speech into text; each finished sentence goes to `/ws/listen` as text.
2. `backend/risk.py` scores the **pattern** across the whole call (official + threat + secrecy + payment/OTP + remote app + refund trick). An alert needs two categories including a dangerous one; genuine bank safety advice is ignored.
3. The flags map onto the four-step playbook, and Ruko warns about the **next** step.
4. The browser speaks the warning, or plays the family member's own recording; the mic is ignored while Ruko speaks.
5. On hang-up the server builds the complaint pack from what was said.

## Run it locally

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn backend.app:app --port 8870
```

Open http://localhost:8870/app/ in Chrome. No API key is needed. Browsers only allow the microphone on localhost or HTTPS. Run the tests with `.venv/Scripts/python -m pytest -q`.

Deploy anywhere that runs Python with WebSockets; [`render.yaml`](render.yaml) is a free Render blueprint.

<details>
<summary><b>Pages and API</b></summary>

- `/`: landing page. `/app/`: Call Guard (live captions, scam-step tracker, red alert, report, sample calls). `/family/?c=<code>&n=<name>`: Family Shield. `/check/`: check messages, links, UPI requests and numbers; number reports; Scam Radar. `/account/`: family account (Supabase Auth). `/privacy/`, `/terms/`, `/licenses/`, `/contact/`.
- `WS /ws/listen?lang=<code>&family=<code>`: send `{"type":"line","text":...}` per sentence, then `{"type":"hangup"}`; receive `transcript`, `warning` and `pack` events.
- `POST /v1/score` (header `X-Ruko-Key`; the key `demo` works for up to 20 lines): returns `level`, `score`, `flags`, `playbook` for transcript lines.
- `POST /api/check`: message/link/UPI/number verdict (rules only, nothing stored).
- `POST/GET/DELETE /api/family/voice`: a family member's consented 5–30 s recording of the warning (memory only, deletable).
</details>

<details>
<summary><b>Data, privacy and push alerts</b></summary>

- No call audio reaches Ruko's server. Chrome's speech recognition may send audio to Google's speech service; the privacy page says so plainly.
- Supabase (Mumbai), row-level security on every table: `leads`, `families`, `alerts`, `number_reports` (server-side flood limits, reporter stored only as a hash). Alerts store time, level and steps only: no audio, words or numbers.
- Family push alerts use Web Push: set `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY`.
</details>

<details>
<summary><b>Android app</b></summary>

[`android/`](android) is a native call-screening app: incoming calls from unknown numbers are looked up in Ruko's community reports and warned about while they ring. It never blocks calls and reads no contacts or SMS. Build it with `cd android && ./gradlew assembleDebug`. Not yet tested on real devices. See [docs/ANDROID_PLAN.md](docs/ANDROID_PLAN.md).
</details>

## History

Ruko was first built by the same developer for an earlier AI challenge, on a commercial speech API. For this hackathon it was rebuilt as an open digital public good: the paid speech service, voice cloning and the phone-line mode were removed, speech now runs in the browser, and the code is MIT licensed. Test numbers from the old speech engine were dropped rather than carried over.

## Project docs

[Evaluation](docs/EVALUATION.md) · [Android plan](docs/ANDROID_PLAN.md) · [Pilot kit](docs/PILOT_KIT.md) · [Translation review](docs/TRANSLATION_REVIEW.md)

## Licence

MIT. See [`LICENSE`](LICENSE).
