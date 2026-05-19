# Editor

> **How to assemble the final HTML briefing** from the per-section research
> memos. Apply this once after all sections are researched.

You're the editor. Researchers handed you memos with 3-4 stories per section.
Your job: turn them into one HTML file styled with the project stylesheet,
save it, tell the user where it is.

## Inputs

- Per-section research memos (see `agents/researcher.md` for the shape)
- `templates/style.css` — the project stylesheet. **Do not fetch this file.**
  Link it in the output's `<head>` with a `<link rel="stylesheet">` pointing
  to its GitHub Pages URL. The browser loads it directly when the user opens
  the file.
- `examples/sample.html` — the structural reference. Use the same floating
  nav, hero, section, card, sources footer, and script tags.

## What you produce

**One file**, written to the user's current working directory:

```
ai-daily-YYYY-MM-DD.html
```

The file's `<head>` must contain:

```html
<link rel="stylesheet" href="https://raff-dev.github.io/ai-daily/templates/style.css">
```

Do NOT inline the stylesheet. Do NOT fetch it via WebFetch and embed it.
The CDN-hosted link is the contract — it keeps the output small and lets
every briefing pick up future style updates automatically.

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

## Floating navigation (required)

Do NOT render a full-width sticky masthead. Instead, place a single compact
floating pill in the top-right corner with up to three things:

1. A "Home" link back to the upstream landing page (so the reader can always
   return to the project)
2. A language toggle (only if you produced a bilingual output)
3. A GitHub icon linking to the source repo

```html
<nav class="floating-nav" aria-label="Primary">
  <a href="https://raff-dev.github.io/ai-daily/" title="Back to landing"><span class="arrow">←</span>&nbsp;Home</a>
  <!-- omit .lang-toggle if there is only one language -->
  <div class="lang-toggle" aria-label="Language">
    <button type="button" class="active" data-set-lang="en">EN</button>
    <button type="button" data-set-lang="pl">PL</button>
  </div>
  <a href="https://github.com/Raff-dev/ai-daily" target="_blank" rel="noopener" class="icon-only" aria-label="Source on GitHub" title="Source on GitHub">
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.185 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.013-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.891 1.529 2.341 1.088 2.91.832.091-.647.349-1.088.635-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.026 2.747-1.026.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482C19.138 20.203 22 16.447 22 12.021 22 6.484 17.523 2 12 2z"/></svg>
  </a>
</nav>
```

If the user is on a fork with its own GitHub Pages URL, replace the Home
`href` with that landing URL.

Do NOT include:

- a full-width sticky masthead bar
- a section-jump nav (Developer Tools / Robotics / …) — the report itself
  is short enough to scroll
- a "Structured" / "Strukturalny" version badge
- an "AI Daily" wordmark in the nav — the hero already brands the page

The `.floating-nav` CSS class is defined in `templates/style.css`, which
loads via the `<link>` in `<head>`.

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

- Card image placeholder with optional preview image (see below)
- Tag badges (section + severity)
- Article title
- One-sentence deck (subtitle)
- Optional stat row (1-3 highlight numbers)
- Bullet list of facts (3 items typical)

### Card preview image (try to include, fall back gracefully)

For each story, attempt to fetch the source page's `og:image` (or
`twitter:image`) meta tag and inject it as `<img class="card-image">`
inside the `card-image-placeholder`. If the image fails to load, the
inline `onerror` removes it and the standard "no preview" SVG shows
through underneath.

Use the standard "no preview" SVG below for **every** card — do NOT
generate a custom decorative SVG with section letters or shapes. The
SVG is just a fallback when there's no image; it should look like a
plain "no image" placeholder, not a section badge.

Pattern (use this exact SVG, change only the `--accent` color):

```html
<div class="card-image-placeholder has-image" style="--accent: #2563EB;">
  <img class="card-image" src="<OG_IMAGE_URL>" alt="" loading="lazy"
       referrerpolicy="no-referrer"
       onerror="this.remove(); this.parentElement.classList.remove('has-image');">
  <svg class="card-visual-svg" viewBox="0 0 640 280" role="img" aria-label="No preview available" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(264, 88)" stroke="#9CA3AF" stroke-width="3" fill="none" stroke-linejoin="round">
      <rect x="0" y="0" width="112" height="104" rx="10"/>
      <circle cx="32" cy="34" r="10" fill="#9CA3AF" stroke="none"/>
      <path d="M0 84 L38 56 L60 70 L86 42 L112 66 L112 104 L0 104 Z" fill="#9CA3AF" stroke="none" opacity="0.45"/>
    </g>
  </svg>
</div>
```

Many publishers either block scraping or omit `og:image`. For those
stories drop the `<img>` entirely (keep the SVG) and do NOT add the
`has-image` class.
- For breakthrough/important stories: extended block with context paragraphs,
  optional quote, "Implications" line
- Card footer with source link + publication date

## Validate before saving

Run through this list. If anything fails, fix it — do not save broken output.

- ✅ Starts with `<!DOCTYPE html>`
- ✅ `<head>` contains `<link rel="stylesheet" href="https://raff-dev.github.io/ai-daily/templates/style.css">`
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
