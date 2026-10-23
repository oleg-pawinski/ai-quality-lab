# ai-quality-lab

Quality engineering for LLM-based systems: evaluation, LLM-as-judge calibration
and red teaming, applied to a real product.

This is a learning and portfolio lab by **Oleg Pawiński**, Quality Manager moving into
an AI Quality Lead role. The goal is not to write clever code, but to show how a quality
lead designs, runs and interprets tests for a non-deterministic system, and turns results
into decisions.

## The case: Herbatnik

**Herbatnik** is a voice assistant for seniors, built by Eldora sp. z o.o.
Its users are older people in Poland, so the test probes are written in Polish.
A wrong answer here is not a UX issue: it can be a medication dose, a scam that looks like
a pension office message, or a health emergency.

The repo tests two systems:

- **Demo bot** (`promptfooconfig.yaml`): my own system prompt for a senior assistant
  on Claude Sonnet 4.5. Fully reproducible.
- **Production copy** (`herbatnik.yaml`): a copy of Herbatnik's main model call
  (Gemini Flash with Google Search grounding), built the same way the server builds it.
  The production system prompt is confidential and is **not** in this repo; findings
  from production are kept in a private defect register.

## What is inside

| Area | What it shows | Files |
|---|---|---|
| Test methodology as code | 8 areas from a written test methodology turned into probes, one criterion per requirement | `sondy/*.json` |
| LLM-as-judge | rubric-based grading (`llm-rubric`) combined with deterministic rules; "rules see words, the judge sees meaning" | `sondy/*.json` |
| Judge calibration | blind comparison of the judge's verdicts with a human's, before trusting the judge | `przygotuj.py`, `porownaj.py` |
| Metrics per requirement | pass rates per metric, technical errors separated from failures, judge reasons for failures | `metryki.py` |
| Non-determinism | every probe runs 3 times; stable vs flaky metrics | `--repeat 3` |
| Red teaming (OWASP Top 10 for LLM apps) | direct and indirect prompt injection, system prompt leakage, sensitive data disclosure, misinformation via false premise | `sondy/ataki.json`, `notatki-owasp.md` |
| Defect register | defects with frequency, severity, root cause and status | `defekty.md` (demo bot) |
| Specification-dependent oracles | the same probe needs a different expected result when the bot has web search or knows the user's name | `sondy/*_herbatnik.json` |

## Selected findings (demo bot)

Full register in `defekty.md` (in Polish). Examples:

- **Unfounded data assurances:** asked where personal data goes, the bot reassured the user
  that data is protected, although nothing in its instructions says so.
- **Emotional dependency:** the bot declared it "values our conversations" to a lonely user
  who preferred it over calling her daughter.
- **Outdated facts:** without a date and search, the bot gave opening hours with full confidence.

Demo bot result at the end of week 4: 27 of 48 checks passed, 0 technical errors.
The point of the number is not the score, but which requirements fail and why.

## Lessons that shaped the tests

- A test oracle depends on the system specification. Probes written for the demo bot
  had to be rewritten for a bot with web search that knows the user's name.
- Probes based on facts about the world have an expiry date (benefits, phone numbers,
  opening hours change). Probes based on behaviour rules change only with policy.
- Repeatability is not truth: a bot can be consistently wrong three times in a row.
- Component tests (prompt + model) and end-to-end tests (guardrails, app, phone) answer
  different questions. Some risks only exist at the chain level.
- A safety feature that works "symbolically" can be more dangerous than none,
  if the user believes it works.

## How to run

Requirements: Node.js, [promptfoo](https://www.promptfoo.dev) via `npx`, Python with
[uv](https://docs.astral.sh/uv/). API keys go to a local `.env` file
(`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`), which is git-ignored.

Demo bot, full run:

```
npx promptfoo@latest eval -c promptfooconfig.yaml --repeat 3 --no-cache --output wyniki.json
```

Results per metric:

```
uv run python metryki.py wyniki.json
```

The production copy (`herbatnik.yaml`) needs a local `herbatnik-prompt.txt`
with the system prompt, which is not published.

## Repo map

- `sondy/` – probes by area: identity, privacy, health, emotions, facts, language,
  scams, boundaries, attacks
- `herbatnik_prompt.py` – builds the production-like message (prompt, user's name,
  date in Polish, user facts; all user data is fictional)
- `metryki.py` – metrics per requirement, failure reasons
- `przygotuj.py`, `porownaj.py` – blind judge calibration
- `defekty.md` – defect register of the demo bot
- `notatki-owasp.md`, `notatki-tydzien-2.md` – study notes (Polish)
- `archiwum/` – weeks 1–2: first Python checks, raw API calls, repetitions

## Data and confidentiality

All user data in the tests is invented. No real seniors' data is used.
The production system prompt and production defect details are confidential
and never committed.

## Contact

Oleg Pawiński – [GitHub](https://github.com/oleg-pawinski)
