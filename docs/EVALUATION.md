# Evaluation

Honest numbers only. Every figure here can be reproduced from this repository.

## Call checker (the scam engine)

The call checker reads what was said on a call and tracks the four scam steps (pretend, scare, isolate, ask). It is tested in `tests/test_risk.py` and `tests/test_startup.py`. Reproduce with `.venv/Scripts/python -m pytest`.

| Test set | What it is | Result |
|---|---|---|
| Real machine transcripts, scam | 14 scripted scam calls in 6 languages, spoken by synthetic voices and transcribed by a speech engine, recognition mistakes kept | 14/14 raise the alarm |
| Real machine transcripts, genuine | 8 genuine calls (bank reminders, delivery OTP, family) transcribed the same way | 0/8 false alarms |
| Written sample calls | 17 scam and 8 genuine scripts in 10 languages, shipped in the app's "sample call" menu | every scam alarms, no genuine call does |
| Ruko's own warning | The spoken warning must not trigger the checker when the mic hears it | passes |

All calls are synthetic: scripts we wrote, never real people.

## Live listening: not measured yet

Ruko now hears calls with the speech recognition built into the user's browser (Web Speech API), so it needs no paid speech service. **We have not yet measured how fast or how reliably that catches a scam on a real speakerphone.** Earlier numbers from a commercial speech engine no longer apply and have been removed. Numbers from real use will be added here, with how they were counted.

## Message checker (SMS, WhatsApp, links)

Two synthetic sets, each written by a separate writer who never saw the checker's rules (`eval/messages.json`, `eval/messages_test.json`). Reproduce with `.venv/Scripts/python -m eval.messages_eval messages_test`. "Warned" means Ruko said *Be careful* or *Scam*. Masked numbers in the data (`97XXXX4410`) are filled with digits before checking, because real messages carry real numbers.

| Set | Use | Precision | Recall | False alarms |
|---|---|---|---|---|
| Set 1, first blind run | before any changes | 85% | 68% (41/60) | 7/60 |
| Set 1, after improving the rules | used to improve the rules, so this number is optimistic | 100% | 92% (55/60) | 0/60 |
| **Set 2, held out** | **scored once, nothing changed afterwards** | **92%** | **72% (36/50)** | **3/50** |

The held-out set is the honest number. All 12 held-out scams with a risky link or APK were caught. What rules still miss: new scripts with no link, such as fake army buyers on OLX, "pay GST to release your LIC bonus", and polite "accidentally sent you money" messages. False alarms come from genuine ride and delivery messages that ask you to share an OTP with the driver or courier. Next step: a small trained classifier alongside the rules, evaluated the same way on a new held-out set.
