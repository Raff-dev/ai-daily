# AI Daily — Agent Instructions

This repository generates a daily AI news briefing automatically via GitHub Actions and publishes it to GitHub Pages.

## Project overview

- `agent.md` — the coverage brief: topics, sections, and search queries the report covers
- `agents/section-researcher.md` — per-section researcher agent prompt
- `agents/editor.md` — evidence-backed synthesis editor prompt
- `agents/translate-agent.md` — Polish translation agent prompt
- `run.py` — the Python runner that calls the AI provider, validates output, and renders HTML
- `outputs/` — generated HTML reports (one file per day)
- `index.html` — auto-rebuilt archive page

## How to customize

**To change the news topics**, edit `agent.md`. This is the only file you normally need to change. Examples of what to modify:

- The **coverage list** at the top (e.g. replace "AI Developer Tools" with "Travel Industry News")
- The **search queries** in each section block
- The **section IDs** and titles if you want different categories

Everything else (HTML layout, CSS, validation logic, rendering) lives in `run.py` and the other agent files — leave those unchanged unless you want to redesign the output.

## Running locally

```bash
git clone https://github.com/<you>/ai-daily
cd ai-daily
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PERSONAL_ACCESS_TOKEN=github_pat_...  # GitHub PAT with Copilot requests: write
python run.py
```

The report is saved to `outputs/AI_Daily_YYYY-MM-DD.html`.

## Key constraint

Do not write files outside `outputs/`, `index.html`, and `.copilot-output/` (which is gitignored). The CI workflow will reject commits that touch anything else.
