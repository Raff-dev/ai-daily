# Translator (optional)

> **Use this only if the user asked for a translation** (e.g. *"...generate
> me a briefing in Polish"* or *"...with a Polish translation"*). If they
> didn't, ignore this file.

## What to translate

The reader-facing copy in the HTML output:

- Hero title and tagline
- Section titles
- Breaking banner text (if present)
- Article titles, decks (subtitles), bullet facts, body paragraphs, implications
- Quote text and citation
- Footer labels (`Generated`, `Time window`, `Sources analyzed`)

## What to keep in English (or original language)

- Source publisher names (unless they have a well-known localized version)
- Source URLs (always)
- Product names, company names, model names
- Numbers and units
- Proper nouns
- Dates (use ISO `YYYY-MM-DD` for the filename and machine-readable bits;
  human-friendly date format in the hero can be localized)

## Style

- Translate naturally, not literally — the result should read like it was
  written by a native speaker who knows the topic
- Keep the tone concise, factual, business/tech oriented
- Don't make headlines clickbait
- If the user asked for Polish (`pl-PL`): use professional, modern Polish.
  Avoid Anglicisms where a clean Polish word exists.

## How to produce a bilingual output

If the user wants both languages in one file:

- Add a small language toggle in the masthead (English / Polish)
- Wrap each language's content in `<div class="report-panel"
  data-lang="en|pl">` and toggle with a tiny inline `<script>`
- This keeps the file self-contained — no separate file per language

If the user wants only the translated version, skip the toggle and just
produce the translated HTML.
