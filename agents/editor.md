# Editor

> **How to assemble the final HTML briefing** from the per-section research
> memos. Apply this once after all sections are researched.

You're the editor. Researchers handed you memos with 3-4 stories per section.
Your job: turn them into one self-contained HTML file styled with the project
stylesheet, save it, tell the user where it is.

## Inputs

- Per-section research memos (see `agents/researcher.md` for the shape)
- `templates/style.css` — the project stylesheet (fetch from the repo, inline
  the full content into a `<style>` tag in your output)
- `examples/sample.html` — the structural reference. Use the same masthead,
  hero, section, card, sources footer, script tags.

## What you produce

**One file**, written to the user's current working directory:

```
ai-daily-YYYY-MM-DD.html
```

Self-contained: CSS inline, no external CSS link, no build step needed. The
file must open correctly with no internet (Lucide icons are fine to load from
CDN — they degrade gracefully without it).

## Layout rules

Per section:

| Position in section | CSS class | Grid span |
|---|---|---|
| 1st story (lead) | `news-card featured` | 7 cols |
| 2nd story | `news-card secondary` | 5 cols |
| 3rd-4th stories | `news-card standard` | 6 cols each |
| Full-width story (rare) | `news-card full` | 12 cols |

If a section has only 1-2 stories, use `featured` for the first, `secondary`
for the second.

## Masthead back link (required)

Include a "back" link as the first element inside `.masthead-inner`, pointing
to the upstream landing page so the reader can always return to the project
catalog:

```html
<a class="masthead-back" href="https://raff-dev.github.io/ai-daily/" title="Back to AI Daily" aria-label="Back to AI Daily"><i data-lucide="arrow-left"></i></a>
```

If the user explicitly told you they're working in a fork with its own
GitHub Pages URL, replace the `href` with that fork's landing URL. Otherwise
default to `https://raff-dev.github.io/ai-daily/` — the user can edit it later.

The `.masthead-back` CSS class is defined in `templates/style.css` (next to
`.masthead-github`). It must be in the inline `<style>` block of the output.

## Hero stats

The hero shows three numbers:

- `{ARTICLES_REVIEWED}` — total stories you actually selected (sum across sections)
- `{SECTIONS_COUNT}` — number of sections that ended up with stories
- `{SOURCES_COUNT}` — number of unique source URLs across all stories

Compute these from your inputs. Don't make them up.

## Breaking banner — only if real

If something genuinely qualifies as breaking news (a major announcement
released in the last few hours, market-moving, headline-grade), put it in the
breaking banner. Otherwise remove the banner block entirely. Do not pad.

## Badges

Use these badge classes per section (match the section `id`):

- `badge-dev`, `badge-robot`, `badge-defense`, `badge-space`,
  `badge-startup`, `badge-market`

Plus a severity badge per article:

- `badge-breakthrough` — industry-defining
- `badge-important` — significant
- `badge-info` — newsworthy but routine
- `badge-unverified` — only if researcher marked it unverified

If your section IDs don't match the defaults (because the user picked custom
topics), pick the closest badge class by visual color, OR use only the
severity badge and skip the section badge.

## Sources footer

Group all source URLs by section, listed under the section title. Use the
exact canonical URLs from the research memos. One source = one `<li>` with a
text link to the publisher.

## Article card structure

Each card follows the structure in `examples/sample.html`. Required parts:

- Card image placeholder (Lucide icon for the section)
- Tag badges (section + severity)
- Article title
- One-sentence deck (subtitle)
- Optional stat row (1-3 highlight numbers)
- Bullet list of facts (3 items typical)
- For breakthrough/important stories: extended block with context paragraphs,
  optional quote, "Implications" line
- Card footer with source link + publication date

## Validate before saving

Run through this list. If anything fails, fix it — do not save broken output.

- ✅ Starts with `<!DOCTYPE html>`
- ✅ `<style>` block contains the full `templates/style.css` content
- ✅ Every article's source URL is a real primary source (not Google News etc.)
- ✅ Every publication date is within the last 24 hours OR the article is
   marked unverified
- ✅ No section is empty — if a section has no stories, omit it entirely
   (and decrement `SECTIONS_COUNT`)
- ✅ Hero stat numbers match what's actually in the file
- ✅ Lucide script tag is present: `<script>lucide.createIcons();</script>`
- ✅ Filename is `ai-daily-YYYY-MM-DD.html` in the user's working directory

## Save and report

After saving, tell the user one short sentence:

> `"Saved to ./ai-daily-2026-05-18.html — double-click to open."`

Don't summarize the news. The file is the deliverable.
