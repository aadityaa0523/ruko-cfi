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

Five synthetic sets, each written by a separate writer who never saw the checker's rules. "Warned" means Ruko said *Be careful* or *Scam*. Reproduce with `.venv/Scripts/python -m eval.messages_eval <set>` (sets are in `eval/`). Masked numbers (`97XXXX4410`) are filled with digits first, because real messages carry real numbers.

| Set | Role | Precision | Recall | False alarms |
|---|---|---|---|---|
| Set 1 (120) | used to improve the rules, so optimistic | 100% | 93% (56/60) | 0/60 |
| Set 2 (100) | first held-out set, scored once in November; later rules changed after the page's own example failed | 95% | 82% (41/50) | 2/50 |
| Set 3 (121) | used to improve the rules in the final round, so **optimistic** | 100% | 98% (60/61) | 0/60 |
| Set 4 (120) | blind, rules frozen in git commit `0b145db` before it was ever run; first run (we then fixed some of its false alarms) | 84% | 87% (52/60) | 10/60 |
| **Set 5 (120)** | **blind, written after the fixes; rules frozen in `5fe7a8c`; first run, nothing changed afterwards** | **92%** | **90% (54/60)** | **5/60** |

**The honest number is set 5, first run:** 90% of scams warned (54/60), 92% precision, and 5 of 60 genuine messages (8%) wrongly warned about. It is the first set written *after* the false-alarm fixes, so it measures them fairly. Set 4's first run, before those fixes, was 87% recall with 10 of 60 genuine messages wrongly flagged; the rules before the November rounds scored 75% recall on set 4.

What still goes wrong on set 5: ride and delivery OTP notices (a code printed for the driver or delivery agent), one bank "never share your OTP" notice, and scams that are gift-parcel, instant-loan-fee or scheme (PM-Kisan, scholarship) messages worded in new ways. Each of these was seen after the run and is not fixed here, so that the number stays honest.

Next step: a sixth blind set after the remaining fixes, and a small trained classifier alongside the rules.
