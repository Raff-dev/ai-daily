# AI Daily — Agent Instructions

You are an AI assistant that just received a prompt like:

> *"Read https://github.com/Raff-dev/ai-daily and generate me a news briefing
> about [topics]. Save it as an HTML file I can open."*

This file tells you exactly what to do.

---

## Project mission — READ THIS FIRST

**The absolute purpose of this repository is to show people starting with AI
how to build a small, useful tool and make it their own.**

This is a learning project disguised as a working utility. Every decision in
this repo — prompts, docs, structure — must serve that goal.

When you propose changes, prefer:

- **Clarity over cleverness** — a 30-line obvious instruction beats a 10-line clever one
- **Few files over many** — a new file must pay for itself in understandability
- **One config touchpoint** — `agents/coverage.md` is THE customization story; do not fragment it
- **Boring tech** — plain Markdown, plain HTML, plain CSS; no frameworks
- **Comments where a beginner would stumble** — explain *why*, not *what*

Before introducing an abstraction, ask: *"Will a person who just learned
Markdown follow this in one sitting?"* If not, find a simpler shape.

---

## The user contract

The user does **exactly one thing**: they type a prompt. That prompt is the
only step in their flow. You do everything else and hand them a single
HTML file in their working directory.

You must NOT:

- Ask the user to fork the repo
- Ask the user to clone the repo
- Ask the user to install anything
- Ask the user to create accounts, secrets, or API keys
- Ask the user to set up GitHub Pages, CI, or any deployment
- Spawn long clarifying dialogs — if the user gave topics, run with them;
  if they didn't, use the defaults in `agents/coverage.md`

You produce: **one HTML file** saved in the user's current working directory,
named `ai-daily-YYYY-MM-DD.html`. The file links to the project stylesheet
hosted on GitHub Pages — keep `<link rel="stylesheet">` instead of inlining
the CSS. Tell the user where you saved it.

---

## Generation playbook (follow in order)

### 1. Read the repo's instructions

Fetch these files from the **GitHub Pages mirror** of this repo:

- `https://raff-dev.github.io/ai-daily/agents/coverage.md` — default topics and search strategy (fallback if user didn't specify topics)
- `https://raff-dev.github.io/ai-daily/agents/researcher.md` — how to research a single section
- `https://raff-dev.github.io/ai-daily/agents/editor.md` — how to assemble the final briefing
- `https://raff-dev.github.io/ai-daily/examples/sample.html` *(optional)* — reference for HTML structure

You do NOT need to fetch `templates/style.css` — the generated briefing
links to it by URL, so the browser loads it directly.

> ⚠️ **Do NOT use `raw.githubusercontent.com` URLs.** Several AI clients
> (notably the Claude mobile app) block that domain, and it serves files
> as `text/plain` with `nosniff` — which breaks `<link rel="stylesheet">`
> in browsers. The GH Pages mirror above serves the same files with
> proper `Content-Type` headers and CORS enabled.

If the user pointed you at a fork (e.g. `github.com/alice/ai-daily`), use
that fork's Pages URL instead: `https://alice.github.io/ai-daily/...`.

### 2. Decide the topics

- If the user named topics in their prompt → use those. Map them to 3-6
  sections (one section per coherent topic).
- If the user did NOT name topics → use the defaults from `agents/coverage.md`.

For each section, pick:
- `id` — short kebab-case slug
- `title` — short human-readable title
- `color` — a hex color for the divider (pick something that fits the topic)
- `icon` — a [Lucide icon name](https://lucide.dev) that fits the topic
- `badge` — a 2-3 letter visual code (e.g. "DEV", "FOOT", "POL")

### 3. Research each section

For each section, follow `agents/researcher.md`. Use your built-in web search
to find news from the **last 24 hours**, verify dates and sources, and pick
3-4 strongest stories per section.

Skip a section entirely if there is no genuine last-24h news on the topic.
Do not fabricate filler.

### 4. Assemble the briefing

Follow `agents/editor.md` to compose the final HTML, structured according to
`examples/sample.html`. In the output's `<head>`, link the project stylesheet:

```html
<link rel="stylesheet" href="https://raff-dev.github.io/ai-daily/templates/style.css">
```

Do NOT inline the CSS into a `<style>` block — it bloats the output and
forces you to re-fetch the stylesheet every run. The `<link>` lets the
browser load it directly with proper caching.

### 5. Validate before saving

Quick checklist:

- ✅ HTML parses (balanced tags)
- ✅ Every article has a working URL, source name, publication date
- ✅ Every URL is a primary source — NOT Google News, Bing, Yahoo, MSN, AOL
  or other aggregators
- ✅ Publication dates are within the last 24 hours (or marked `UNVERIFIED`)
- ✅ The `<head>` contains `<link rel="stylesheet" href="https://raff-dev.github.io/ai-daily/templates/style.css">`
- ✅ Filename is `ai-daily-YYYY-MM-DD.html`
- ✅ Every card-image URL returns HTTP 200. Run
  `bash scripts/verify-images.sh <output-file>` (or fetch the script from
  `https://raff-dev.github.io/ai-daily/scripts/verify-images.sh` if the
  user isn't inside a clone). If any URL fails, re-run the image fallback
  chain in `agents/editor.md` for that card before saving.

If validation fails, fix it — do not save a broken briefing.

### 6. Save and report

Write the file to the user's current working directory. Then tell the user
**exactly one sentence**: where the file is, and that they can double-click
it to open. Don't summarize the news content — that's what the file is for.

Example: `"Saved to ./ai-daily-2026-05-18.html — double-click to open."`

---

## Output contract

The HTML file you produce must:

1. Start with `<!DOCTYPE html>`
2. Link the project stylesheet: `<link rel="stylesheet" href="https://raff-dev.github.io/ai-daily/templates/style.css">`
3. Use only CSS classes defined in that stylesheet
4. Reference Lucide icons via the CDN script tag (already in `examples/sample.html`)
5. Be valid HTML — no broken tags, no JavaScript errors

The structural skeleton lives in `examples/sample.html`. Treat it as the
contract for layout: same masthead, same hero, same section structure, same
card variants (`featured`, `secondary`, `standard`, `full`), same footer.

---

## When the user asks to modify the repo itself

Sometimes the user will say *"fork this repo and change the default topics to X"*
or *"edit the styles to use a dark theme"*. In that case:

1. Fork the repo (or have them fork — clarify if you can't)
2. Edit `agents/coverage.md` for default topics and search strategy
3. Edit `templates/style.css` for visual changes
4. Edit `examples/sample.html` if structural changes are needed
5. Do **not** edit `AGENTS.md` unless the user is explicitly changing the
   contract — it is the source of truth for every AI assistant that reads
   this repo

`CLAUDE.md` and `.github/copilot-instructions.md` are symlinks to `AGENTS.md`.
Don't break them.

---

## What this repo does NOT do

To set expectations clearly:

- No daily cron — the user generates a briefing whenever they ask
- No GitHub Pages deploy — the output lives on the user's disk
- No API keys, secrets, or PATs — your AI subscription does the work
- No Python, no `run.py`, no `requirements.txt` — nothing to install
- No CI workflow — there's nothing to test or deploy

If you find yourself proposing one of these, stop. It contradicts the mission.
