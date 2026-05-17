# AI Daily — Agent Instructions

This repository generates a daily news briefing automatically via GitHub Actions and publishes it to GitHub Pages. An AI agent fleet searches the web, verifies sources, and renders a polished HTML report every morning.

## What to do when a user asks you to set this up

1. **Fork** `https://github.com/Raff-dev/ai-daily` into the user's GitHub account.
2. **Customize** `agents/coverage.md` — this is the only file the user needs to change. Update the topics, section names, and search queries to match what the user wants.
3. **Tell the user to do 2 things manually** (you cannot do these for them):
   - Add a `PERSONAL_ACCESS_TOKEN` secret in **Settings → Secrets and variables → Actions** (GitHub PAT with `Copilot requests: write` permission)
   - Enable GitHub Pages in **Settings → Pages**, source: **GitHub Actions**

Once those two steps are done, the workflow runs automatically every day at 05:00 UTC.

## Repository structure

```
agents/coverage.md          ← the ONLY file to edit when customizing
agents/section-researcher.md  agent prompt: per-section web research
agents/editor.md              agent prompt: evidence-backed synthesis
agents/translate-agent.md     agent prompt: Polish translation
agents/orchestrator.md        documents the pipeline contract
run.py                        Python runner — do not edit for customization
.github/workflows/daily.yml   CI schedule and deployment
outputs/                      generated HTML reports (one per day)
index.html                    auto-rebuilt archive page
```

## How to customize

Edit `agents/coverage.md`. This file defines:
- The **coverage list** — what topics the briefing covers
- The **search queries** — what the agents actually search for
- The **section IDs and names** — what categories appear in the report

Everything else (HTML layout, validation logic, rendering) is in `run.py` — leave it unchanged.

Example: to change from AI news to travel industry news, update the coverage list and queries in `agents/coverage.md` to focus on flights, hotels, airline stocks, and tourism startups.

## What not to change

Do not edit `run.py` unless redesigning the output format. Do not write files outside `outputs/`, `index.html`, and `.copilot-output/` (gitignored). The CI workflow will reject commits touching anything else.
