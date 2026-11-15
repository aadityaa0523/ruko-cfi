# Impact plan (written before counting began)

This file fixes, in advance, what Ruko counts and what would count as success, so the results on [/impact/](../web/impact/index.html) can't be reinterpreted after the fact. Its date in the git history is the proof of when it was written. Any later change to this plan will be a new commit with the reason stated, and the results page will say so.

## Question

Does Ruko reach real people, and does it change what they do when a scam reaches them?

## What is counted (anonymous)

| Measure | Counted as |
|---|---|
| Reach | Distinct random device ids; distinct connections (salted hash) |
| Use | Messages checked, live calls protected, sample calls, family links shared, family screens opened, numbers reported |
| Scams caught | Checks Ruko flagged as scam or suspicious; live call warnings |
| Behaviour (self-reported) | After a warning: "were you about to reply, click, share an OTP or pay?" and, after a scam call, "did you hang up before sharing an OTP or sending money?" |
| Learning | Spot-the-scam test: 6 messages before, 6 different messages after learning the four signs; set order randomised per device |

Never stored: message text, phone numbers, names, raw IP addresses.

## Exclusions

- Our own testing: localhost, and any browser that opened a Ruko page with `?test=1`.
- Flood limits: 120 events per connection per hour, 200 per device per day.
- Each device's quiz counts once (first before-round and first after-round).

## Success rules, fixed now

1. **Reach:** at least 100 distinct devices from at least 50 distinct connections by the end of judging data collection.
2. **Learning:** among people who finish both quiz rounds (at least 30 needed to judge), the average after-score is higher than the before-score, and the 95% paired interval for the change is above zero.
3. **Behaviour:** report the number of "yes, I was about to" answers after warnings as a count, with no extrapolation to the population.

If a rule is not met, the results page will say so plainly. Numbers will never be estimated, rounded up, or extended from a sample to India.

## Known limits

- Device ids are not people: one person on two devices counts twice; a shared phone counts once.
- Behaviour answers are self-reported, and people who answer may differ from people who don't.
- The quiz messages are made up, and a short test measures short-term recognition, not long-term behaviour.
