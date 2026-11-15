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

Four synthetic sets, each written by a separate writer who never saw the checker's rules. "Warned" means Ruko said *Be careful* or *Scam*. Reproduce with `.venv/Scripts/python -m eval.messages_eval <set>` (sets are in `eval/`). Masked numbers (`97XXXX4410`) are filled with digits first, because real messages carry real numbers.

| Set | Role | Precision | Recall | False alarms |
|---|---|---|---|---|
| Set 1 (120) | used to improve the rules, so optimistic | 100% | 93% (56/60) | 0/60 |
| Set 2 (100) | first held-out set, scored once in November; later rules changed after the page's own example failed | 95% | 82% (41/50) | 2/50 |
| Set 3 (121) | used to improve the rules in the final round, so **optimistic** | 100% | 98% (60/61) | 0/60 |
| **Set 4 (120)** | **blind, rules frozen in git commit `0b145db` before it was ever run; first run** | **84%** | **87% (52/60)** | **10/60** |

**The honest number is set 4, first run:** 87% of scams warned, but 10 of 60 genuine messages were wrongly warned about (17%). For comparison, the rules *before* this round scored 75% recall and 82% precision on the same set 4, so recall improved by about 12 points and false alarms did not.

What went wrong on set 4: real OTP and KYC-branch notices in Hindi and Hinglish ("do not share your OTP", "visit your home branch"), ride and delivery codes, and a bank-awareness notice. After seeing set 4 we fixed some of those (false alarms 10 down to 7 on that set, no new ones on the other sets), but **any number measured on set 4 after that is optimistic and is not claimed**. The scams still missed are mostly scheme or subsidy forms (PM-Kisan, Ladli Behna, gas subsidy) worded in new ways.

Next step: a fifth blind set to measure the false-alarm fix honestly, and a small trained classifier alongside the rules.
