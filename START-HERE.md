# Start here

For the first Claude Code session on this repo. Delete this file once the build is running.

---

## Setup before you open Claude Code

**1. Create the repo** as `sr-workshops-mirror` in the **`Sense-Respond`** GitHub org, and push
this folder into it. The org already exists. Decided 2026-09-29; see `PROJECT_BRIEF.md`.

**2. Add the Ti.to token** as a repository secret named `TITO_API_TOKEN`.
Settings, then Secrets and variables, then Actions.
Never paste it into a chat window, including Claude Code.

**3. Authenticate Claude Code with the S&R Learning team account** in this terminal, not your
personal account.

Netlify and DNS can wait until there is something to deploy.

## Then, in the terminal

```bash
cd sr-workshops-mirror
claude
```

First message to Claude Code:

---

Read `PROJECT_BRIEF.md` first, then `docs/FINDINGS.md`, `docs/BRAND-SPEC.md` and
`docs/BUILD-NOTES.md`. Then tell me what you plan to do first and flag anything in the plan you
think is wrong. Don't write code until I confirm.

Context in one line: we're building a static, crawlable page listing our public workshops,
rebuilt daily from the Ti.to API, published to `public/` and served by Netlify at
workshops.senseandrespond.co.

The one thing that matters: it has to be server-rendered HTML. AI crawlers don't run
JavaScript, and that's the entire reason this project exists. `docs/FINDINGS.md` has two dead
ends already ruled out. Don't re-propose them.

`build.py` is half-written. Its Ti.to layer is tested and should be kept. Its render layer
targets an abandoned approach and needs replacing. `docs/BUILD-NOTES.md` says which is which.

You can develop against `docs/sample-workshops.json` without hitting the API.

---

## What Claude Code should not do

- Propose a Ti.to embed widget or a Squarespace code block. Both are in
  `docs/FINDINGS.md` as rejected, with reasons
- Look for a way to put this on senseandrespond.co directly. Squarespace 7.1 cannot do it
- Rewrite the tested Ti.to fetching, date formatting, pricing or dedupe logic

## Repo layout

| Path | What |
|---|---|
| `PROJECT_BRIEF.md` | Living brief. Claude Code updates Current State as it builds |
| `build.py` | The generator. Half-written; see `docs/BUILD-NOTES.md` |
| `public/` | Build output. Netlify's publish directory. Generated, committed |
| `docs/FINDINGS.md` | Verified technical facts, and the dead ends |
| `docs/BRAND-SPEC.md` | Type scale, palette, the workshop date gradient |
| `docs/BUILD-NOTES.md` | What to keep, rewrite and add in `build.py` |
| `docs/TEAM-BRIEF.md` | One-pager for Jeff and Natalia |
| `docs/sample-workshops.json` | Real 15-workshop snapshot for offline development |
| `docs/DEPRECATED-squarespace-code-block.html` | The wrong approach, kept as a record |

## End of session

Ask Claude Code to update `PROJECT_BRIEF.md` before you stop. That's the laptop workflow habit
from `dev-workflow-laptop.md`.
