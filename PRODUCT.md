# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primary (design leads for them): adult children, about 25–40,** often living away from their parents. They set Ruko up for a parent, share the Family Shield link, record the warning in their own voice, and are the ones who would pay. Their job: "make sure my parents don't lose money to a scam call while I'm not there."
- **Protected person: a parent or elder,** often 55+, with low digital literacy, more comfortable in Hindi or a regional language. Their job during a call: get a clear, loud "stop" at the right moment. Their screen must be one big action.
- **Secondary: banks, UPI apps, telcos and cyber cells,** who would buy the scoring API and anonymous scam-trend data.

## Product Purpose
Ruko is a scam-safety app for Indian families. It listens to a phone call on speaker, recognises the scam playbook as it unfolds, warns out loud in the elder's language before the scammer's next move, turns the family member's phone red live, and hands over a ready 1930 complaint after the call. Success: an elder hangs up before sharing an OTP or sending money, and the family knows within seconds.

## Positioning
Other guards check the caller's *number* (Truecaller, telcos) or need a flagship phone and speak Hindi/English only (Google Pixel). Ruko understands *what the caller is saying*, in 10 Indian languages, beside any phone on speaker, and predicts the scammer's next step from the four-step playbook (pretend → scare → isolate → ask). The family is part of the defence, not a notification afterwards.

## Operating Context
- The elder is mid-call, stressed, phone on speaker; the guard screen is read in seconds.
- The adult child is at work; the family screen is glanced at on a phone, often after a push notification.
- After a loss there is a "golden hour" to call 1930 and freeze money.
- Open source (MIT) digital public good for the Code for a Billion hackathon (Code for India); first built for an earlier challenge on a commercial speech API, now free of any paid speech service.

## Capabilities and Constraints
- Built: speakerphone guard using the browser's Web Speech API (Chrome), 10 languages chosen by the user, next-step warnings, spoken warning by the browser voice (elder slow mode), Family Shield live screen, the family member's own recorded warning (no cloning), 1930 complaint pack, message/link/UPI checker, number reports, partner scoring API, pilot waitlist.
- Stack: vanilla HTML/CSS/JS served by FastAPI (`ruko/web/`), no build step. Deployed on Render free plan (sleeps when idle).
- Ruko only warns; it never blocks or ends calls. No call audio reaches the server; only text.
- Undecided: persistent storage (Supabase), custom domain, real telephony number.

## Brand Commitments
- Name: **Ruko** ("stop" in Hindi). Because another Devpost project uses the name, pair it with a descriptor where it first appears.
- Website style (user decision, 10 Nov 2026): premium dark, CRED-style (near-black, white type, electric-lime accent #c8f560, red only for scams, bento feature grid). App screens stay light.
- App visual style (user decision, 9 Nov 2026): a polished mainstream consumer app in the class of Truecaller and similar Indian apps (white surfaces, brand blue #1f5eff, red only for scams, Manrope + Mukta). The earlier road-sign world was rejected as "not like a real product".
- Voice: plain, calm, direct, warm; short sentences; never fear-mongering; Hinglish-friendly.

## Evidence on Hand
- Measured results in `docs/EVALUATION.md`: scam engine on real machine transcripts (14/14 scams, 0/8 false alarms) and a held-out message set (92% precision, 72% recall). Live listening with browser speech recognition is not measured yet.
- 83 automated tests. Loss figures: ₹22,845 Cr cyber fraud and ₹1,935 Cr digital-arrest losses in 2024 (government replies in Parliament).
- **Solo build.** No users, testimonials, partners, press or pilots exist yet: never imply them. All test calls are synthetic. Do not claim the Samarthan shortlisting.

## Product Principles
1. The elder's screen has one job: say "stop" clearly at the right moment.
2. The family is part of the defence; isolation is what scams exploit.
3. Show proof, never claims: measured numbers and honest limits.
4. Free to run and to adopt: no paid speech API, MIT licence.
5. Privacy by default: no audio on the server, deletable voice recording, nothing shared without a link the user controls.

## Accessibility & Inclusion
- Elders: large text, high contrast, big touch targets (≥48 px), plain words, English/Hindi toggle on every screen; regional-language warnings by voice.
- WCAG 2.2 AA; works at 375 px; light and dark; reduced-motion respected; the alert is never colour-only.
