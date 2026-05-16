#!/usr/bin/env python3
"""AI Daily Brief — asks an agent for structured content and renders stable HTML."""

import html
import json
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9


SECTION_CONFIG = {
    "dev-tools": {"title": "Developer Tools", "icon": "monitor", "color": "#2563EB", "badge": "dev"},
    "robotics": {"title": "Robotics", "icon": "bot", "color": "#16A34A", "badge": "robot"},
    "defense": {"title": "Defense", "icon": "shield", "color": "#DC2626", "badge": "defense"},
    "space": {"title": "Space", "icon": "rocket", "color": "#7C3AED", "badge": "space"},
    "startups": {"title": "Startups", "icon": "banknote", "color": "#EA580C", "badge": "startup"},
    "markets": {"title": "Markets", "icon": "bar-chart-2", "color": "#0F766E", "badge": "market"},
}

SYSTEM_PROMPT = """\
You are an AI News Specialist. Generate only structured content for a daily news briefing.
Do not generate HTML, CSS, Markdown, code fences, or explanations.

Use the repository owner's custom brief from agent.md. If it conflicts with default topics,
the custom brief wins.

Process:
1. Run the searches requested by agent.md, replacing {DATE}, {YEAR}, and {MONTH}.
2. Keep only news published in the last 24 hours.
3. Pick max 4 important stories per section.
4. Skip empty sections.
5. Verify dates and sources. Set verified=false if uncertain.
6. Return JSON only.

JSON shape:
{
  "title": "AI Daily",
  "tagline": "Everything you need to know about artificial intelligence from the last 24 hours.",
  "articles_reviewed": 24,
  "breaking": "optional urgent one-sentence item or empty string",
  "sections": [
    {
      "id": "dev-tools",
      "title": "Developer Tools",
      "icon": "monitor",
      "color": "#2563EB",
      "articles": [
        {
          "title": "Short factual headline",
          "subtitle": "One-sentence summary shown in collapsed view.",
          "importance": "breakthrough|important|info",
          "verified": true,
          "stats": [{"number": "2x", "label": "short label"}],
          "facts": ["Fact 1", "Fact 2", "Fact 3"],
          "body": ["Context paragraph 1", "Context paragraph 2"],
          "quote": {"text": "Optional quote", "cite": "Optional source"},
          "implications": "Why this matters.",
          "source_name": "Source",
          "source_url": "https://example.com/article",
          "published_at": "2026-05-16"
        }
      ]
    }
  ]
}

Allowed default section ids: dev-tools, robotics, defense, space, startups, markets.
For custom topics, use lowercase kebab-case ids and include title, icon, and color.
"""

REPORT_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: 'Inter', system-ui, sans-serif; font-size: 15px; line-height: 1.65; color: #111827; background: #F3F4F6; -webkit-font-smoothing: antialiased; }
:root {
  --bg-page: #F3F4F6; --bg-card: #FFFFFF; --text-primary: #111827; --text-secondary: #374151; --text-muted: #6B7280;
  --border: #E5E7EB; --border-strong: #D1D5DB;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08); --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius: 12px; --radius-sm: 8px; --radius-pill: 9999px;
  --dev: #2563EB; --dev-bg: #EFF6FF; --dev-border: #BFDBFE;
  --robot: #16A34A; --robot-bg: #F0FDF4; --robot-border: #BBF7D0;
  --defense: #DC2626; --defense-bg: #FEF2F2; --defense-border: #FECACA;
  --space: #7C3AED; --space-bg: #F5F3FF; --space-border: #DDD6FE;
  --startup: #EA580C; --startup-bg: #FFF7ED; --startup-border: #FED7AA;
  --market: #0F766E; --market-bg: #F0FDFA; --market-border: #99F6E4;
}
[data-lucide] { width: 14px; height: 14px; stroke-width: 2; display: inline-block; vertical-align: -2px; flex-shrink: 0; }
.section-icon [data-lucide] { width: 20px; height: 20px; stroke-width: 1.75; }
.badge [data-lucide] { width: 11px; height: 11px; stroke-width: 2.5; vertical-align: -1px; }
.card-image-placeholder [data-lucide] { width: 48px; height: 48px; stroke-width: 1.25; color: #C4C9D4; }
.page-wrapper { max-width: 1180px; margin: 0 auto; padding: 0 16px 60px; }
.masthead { background: #fff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; box-shadow: var(--shadow-sm); }
.masthead-inner { max-width: 1180px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; gap: 24px; height: 56px; }
.masthead-brand { display: flex; align-items: baseline; gap: 10px; flex-shrink: 0; }
.masthead-title { font-size: 22px; font-weight: 800; letter-spacing: -0.03em; color: #111827; }
.masthead-edition { font-size: 11px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.masthead-nav { display: flex; gap: 4px; flex: 1; overflow-x: auto; scrollbar-width: none; }
.masthead-nav::-webkit-scrollbar { display: none; }
.masthead-nav a { display: flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 500; color: var(--text-secondary); text-decoration: none; white-space: nowrap; transition: background 0.15s; }
.masthead-nav a:hover { background: var(--bg-page); }
.masthead-version { flex-shrink: 0; padding: 4px 12px; background: #111827; color: #fff; border-radius: var(--radius-pill); font-size: 11px; font-weight: 600; }
.hero-header { background: linear-gradient(135deg, #111827 0%, #1e3a5f 100%); color: white; padding: 48px 16px 40px; margin-bottom: 28px; }
.hero-inner { max-width: 1180px; margin: 0 auto; }
.hero-date { font-size: 12px; font-weight: 500; color: #93C5FD; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.hero-title { font-size: 42px; font-weight: 800; letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 12px; }
.hero-title span { color: #60A5FA; }
.hero-tagline { font-size: 15px; color: #9CA3AF; max-width: 520px; line-height: 1.6; margin-bottom: 24px; }
.hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.hero-stat-num { font-size: 28px; font-weight: 700; color: #fff; letter-spacing: -0.03em; display: block; }
.hero-stat-label { font-size: 11px; color: #9CA3AF; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.breaking-banner { background: #FEF2F2; border: 1px solid #FECACA; border-radius: var(--radius-sm); padding: 10px 16px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; color: #991B1B; }
.breaking-tag { background: #DC2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.1em; flex-shrink: 0; display: inline-flex; align-items: center; gap: 4px; }
.news-section { margin-bottom: 36px; }
.section-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius) var(--radius) 0 0; margin-bottom: 2px; }
.section-icon { font-size: 0; line-height: 1; }
.section-meta { flex: 1; }
.section-overline { display: block; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); margin-bottom: 1px; }
.section-title { font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.section-count { font-size: 11px; font-weight: 600; color: var(--text-muted); background: var(--bg-page); border: 1px solid var(--border); padding: 3px 10px; border-radius: var(--radius-pill); }
.section-divider { height: 3px; border-radius: 0 0 3px 3px; margin-bottom: 12px; }
.articles-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
.news-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden; transition: box-shadow 0.15s, transform 0.15s; box-shadow: var(--shadow-sm); }
.news-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.news-card.featured { grid-column: span 7; }
.news-card.secondary { grid-column: span 5; }
.news-card.standard { grid-column: span 6; }
.news-card.full { grid-column: span 12; }
.news-card > summary { list-style: none; cursor: pointer; }
.news-card > summary::-webkit-details-marker { display: none; }
.card-summary { padding: 16px 18px; }
.expand-hint { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600; color: #2563EB; }
.expand-hint [data-lucide] { width: 13px; height: 13px; transition: transform .15s; }
.news-card[open] .expand-hint [data-lucide] { transform: rotate(180deg); }
.card-details { border-top: 1px solid var(--border); padding: 14px 18px 16px; display: flex; flex-direction: column; flex: 1; }
.card-image-placeholder { margin: -14px -18px 14px; width: calc(100% + 36px); aspect-ratio: 16/7; background: linear-gradient(135deg, #F3F4F6, #E5E7EB); display: flex; align-items: center; justify-content: center; font-size: 0; }
.card-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: var(--radius-pill); font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; line-height: 1; white-space: nowrap; }
.badge-dev { background: var(--dev-bg); color: var(--dev); border: 1px solid var(--dev-border); }
.badge-robot { background: var(--robot-bg); color: var(--robot); border: 1px solid var(--robot-border); }
.badge-defense { background: var(--defense-bg); color: var(--defense); border: 1px solid var(--defense-border); }
.badge-space { background: var(--space-bg); color: var(--space); border: 1px solid var(--space-border); }
.badge-startup { background: var(--startup-bg); color: var(--startup); border: 1px solid var(--startup-border); }
.badge-market { background: var(--market-bg); color: var(--market); border: 1px solid var(--market-border); }
.badge-custom { background: #F9FAFB; color: #374151; border: 1px solid #E5E7EB; }
.badge-breakthrough { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
.badge-important { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-info { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.badge-unverified { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.article-title { font-size: 17px; font-weight: 700; line-height: 1.3; color: var(--text-primary); margin-bottom: 8px; letter-spacing: -0.02em; }
.news-card.featured .article-title { font-size: 21px; }
.article-deck { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; margin-bottom: 10px; font-style: italic; }
.bullet-list { list-style: none; margin-bottom: 14px; display: flex; flex-direction: column; gap: 6px; }
.bullet-list li { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; padding-left: 14px; position: relative; }
.bullet-list li::before { content: '•'; position: absolute; left: 0; color: var(--text-muted); font-weight: 700; }
.stat-row { display: flex; flex-wrap: wrap; margin-bottom: 12px; }
.stat-highlight { display: inline-flex; align-items: baseline; gap: 4px; padding: 6px 12px; background: var(--bg-page); border: 1px solid var(--border); border-radius: var(--radius-sm); margin: 4px 4px 4px 0; }
.stat-number { font-size: 22px; font-weight: 700; letter-spacing: -0.03em; color: var(--text-primary); }
.stat-label { font-size: 11px; color: var(--text-muted); font-weight: 500; }
.extended-content { border-top: 1px solid var(--border); margin-top: 12px; padding-top: 12px; }
.body-text { font-size: 14px; color: var(--text-secondary); line-height: 1.68; margin-bottom: 10px; }
.implications { background: #FAFAF9; border-left: 3px solid #D1D5DB; padding: 8px 12px; border-radius: 0 var(--radius-sm) var(--radius-sm) 0; font-size: 13.5px; color: var(--text-secondary); }
.article-quote { border-left: 3px solid var(--border-strong); margin: 12px 0; padding: 8px 14px; }
.article-quote p { font-style: italic; font-size: 15px; color: var(--text-primary); line-height: 1.5; margin-bottom: 4px; }
.article-quote cite { font-size: 11.5px; color: var(--text-muted); font-style: normal; font-weight: 500; }
.card-footer { margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.source-link { display: inline-flex; align-items: center; gap: 5px; text-decoration: none; font-size: 12px; font-weight: 500; color: #2563EB; padding: 4px 10px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: var(--radius-pill); transition: background 0.12s; }
.source-link:hover { background: #DBEAFE; }
.source-link img { width: 12px; height: 12px; border-radius: 2px; }
.pub-time { font-size: 11.5px; color: var(--text-muted); margin-left: auto; }
.report-footer { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px 28px; margin-top: 36px; box-shadow: var(--shadow-sm); }
.footer-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.sources-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }
.sources-section h4 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
.sources-section ul { list-style: none; display: flex; flex-direction: column; gap: 5px; }
.sources-section a { font-size: 12.5px; color: #2563EB; text-decoration: none; }
.sources-section a:hover { text-decoration: underline; }
.footer-meta { border-top: 1px solid var(--border); padding-top: 14px; display: flex; gap: 16px; flex-wrap: wrap; }
.footer-meta p { font-size: 11.5px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; }
@media (max-width: 900px) {
  .news-card.featured, .news-card.secondary, .news-card.standard { grid-column: span 12; }
  .hero-title { font-size: 30px; }
  .masthead-nav { display: none; }
}
"""


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def get_date_info() -> dict:
    warsaw = ZoneInfo("Europe/Warsaw")
    now = datetime.now(warsaw)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "date_long": now.strftime("%B %d, %Y"),
        "date_short": now.strftime("%b %d"),
        "day": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": str(now.year),
        "datetime": now.strftime("%Y-%m-%d %H:%M %Z"),
    }


def load_agent_prompt() -> str:
    prompt_path = Path(os.environ.get("AGENT_PROMPT_PATH", "agent.md"))
    if not prompt_path.exists():
        raise FileNotFoundError(f"Agent prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    return f"{SYSTEM_PROMPT}\n\n## CUSTOM AGENT BRIEF FROM agent.md\n\n{load_agent_prompt()}"


def build_user_message(dates: dict) -> str:
    return (
        f"Generate today's structured AI Daily Brief content.\n\n"
        f"Date: {dates['date']}\n"
        f"Day: {dates['day']}\n"
        f"Month: {dates['month']}\n"
        f"Year: {dates['year']}\n\n"
        "Return JSON only. The app will render HTML."
    )


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("The agent did not return a JSON object.")

    data = json.loads(stripped[start : end + 1])
    if not isinstance(data.get("sections"), list):
        raise RuntimeError("Agent JSON must contain a 'sections' array.")
    return data


def run_anthropic_agent(dates: dict, system_prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    response = client.messages.create(
        model=model,
        max_tokens=20000,
        system=system_prompt,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10,
        }],
        messages=[{"role": "user", "content": build_user_message(dates)}],
    )

    text = "".join(getattr(block, "text", "") for block in response.content)
    return extract_json(text)


def run_command_agent(dates: dict, system_prompt: str) -> dict:
    command = os.environ.get("AGENT_COMMAND", "").strip()
    if not command:
        raise RuntimeError("AI_PROVIDER=command requires AGENT_COMMAND to be set.")

    prompt = f"{system_prompt}\n\n{build_user_message(dates)}\n"
    result = subprocess.run(
        shlex.split(command),
        input=prompt,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("AGENT_TIMEOUT_SECONDS", "1800")),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Agent command failed with exit code {result.returncode}:\n{result.stderr}")
    return extract_json(result.stdout)


def run_agent(dates: dict) -> dict:
    provider = os.environ.get("AI_PROVIDER", "anthropic").strip().lower()
    system_prompt = build_system_prompt()
    if provider == "anthropic":
        return run_anthropic_agent(dates, system_prompt)
    if provider in {"command", "custom"}:
        return run_command_agent(dates, system_prompt)
    raise ValueError(f"Unsupported AI_PROVIDER: {provider}. Use 'anthropic' or 'command'.")


def section_meta(section: dict) -> dict:
    section_id = section.get("id") or "custom"
    defaults = SECTION_CONFIG.get(section_id, {})
    return {
        "id": section_id,
        "title": section.get("title") or defaults.get("title") or section_id.replace("-", " ").title(),
        "icon": section.get("icon") or defaults.get("icon") or "newspaper",
        "color": section.get("color") or defaults.get("color") or "#374151",
        "badge": defaults.get("badge", "custom"),
    }


def article_class(index: int, total: int) -> str:
    if total == 1:
        return "full"
    if index == 0:
        return "featured"
    if index == 1:
        return "secondary"
    return "standard"


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split("/")[0]


def render_stats(stats: list) -> str:
    if not stats:
        return ""
    items = "\n".join(
        f'<div class="stat-highlight"><span class="stat-number">{e(s.get("number"))}</span>'
        f'<span class="stat-label">{e(s.get("label"))}</span></div>'
        for s in stats
    )
    return f'<div class="stat-row">{items}</div>'


def render_article(article: dict, meta: dict, index: int, total: int) -> str:
    importance = article.get("importance") or "info"
    if importance not in {"breakthrough", "important", "info"}:
        importance = "info"
    verified_badge = "" if article.get("verified", True) else (
        '<span class="badge badge-unverified"><i data-lucide="alert-triangle"></i> UNVERIFIED</span>'
    )

    facts = "\n".join(f"<li>{e(fact)}</li>" for fact in article.get("facts", []) if fact)
    facts_html = f'<ul class="bullet-list">{facts}</ul>' if facts else ""
    body = "\n".join(f'<p class="body-text">{e(paragraph)}</p>' for paragraph in article.get("body", []) if paragraph)

    quote = article.get("quote") or {}
    quote_html = ""
    if quote.get("text"):
        quote_html = (
            f'<blockquote class="article-quote"><p>"{e(quote.get("text"))}"</p>'
            f'<cite>{e(quote.get("cite"))}</cite></blockquote>'
        )

    implications = ""
    if article.get("implications"):
        implications = (
            f'<p class="body-text implications"><i data-lucide="lightbulb"></i> '
            f'<strong>Implications:</strong> {e(article.get("implications"))}</p>'
        )

    source_url = article.get("source_url") or "#"
    source_name = article.get("source_name") or domain_from_url(source_url) or "Source"
    domain = domain_from_url(source_url)
    source_html = (
        f'<a href="{e(source_url)}" class="source-link" target="_blank" rel="noopener">'
        f'<img src="https://www.google.com/s2/favicons?domain={e(domain)}&sz=16" alt="">'
        f'{e(source_name)}</a>'
    )

    return f"""
<details class="news-card {article_class(index, total)}">
  <summary class="card-summary">
    <h2 class="article-title">{e(article.get("title"))}</h2>
    <p class="article-deck">{e(article.get("subtitle"))}</p>
    <span class="expand-hint">Read full brief <i data-lucide="chevron-down"></i></span>
  </summary>
  <div class="card-details">
    <div class="card-image-placeholder"><i data-lucide="{e(meta["icon"])}"></i></div>
    <div class="card-tags">
      <span class="badge badge-{e(meta["badge"])}"><i data-lucide="{e(meta["icon"])}"></i> {e(meta["title"])}</span>
      <span class="badge badge-{e(importance)}"><i data-lucide="sparkles"></i> {e(importance)}</span>
      {verified_badge}
    </div>
    {render_stats(article.get("stats", []))}
    {facts_html}
    <div class="extended-content">
      {body}
      {quote_html}
      {implications}
    </div>
    <div class="card-footer">
      {source_html}
      <span class="pub-time">{e(article.get("published_at"))}</span>
    </div>
  </div>
</details>"""


def render_section(section: dict) -> str:
    meta = section_meta(section)
    articles = [article for article in section.get("articles", []) if article.get("title")]
    if not articles:
        return ""
    rendered_articles = "\n".join(render_article(article, meta, index, len(articles)) for index, article in enumerate(articles))
    count_label = "article" if len(articles) == 1 else "articles"
    return f"""
<section class="news-section" id="{e(meta["id"])}">
  <div class="section-header">
    <span class="section-icon"><i data-lucide="{e(meta["icon"])}"></i></span>
    <div class="section-meta">
      <span class="section-overline">Section</span>
      <h2 class="section-title">{e(meta["title"])}</h2>
    </div>
    <span class="section-count">{len(articles)} {count_label}</span>
  </div>
  <div class="section-divider" style="background: {e(meta["color"])};"></div>
  <div class="articles-grid">
    {rendered_articles}
  </div>
</section>"""


def collect_sources(report: dict) -> list[dict]:
    sources = []
    for section in report.get("sections", []):
        meta = section_meta(section)
        items = []
        for article in section.get("articles", []):
            if article.get("source_url"):
                items.append({"name": article.get("source_name") or domain_from_url(article["source_url"]), "url": article["source_url"]})
        if items:
            sources.append({"title": meta["title"], "icon": meta["icon"], "items": items})
    return sources


def render_sources(report: dict) -> str:
    sections = []
    for source_section in collect_sources(report):
        links = "\n".join(
            f'<li><a href="{e(item["url"])}" target="_blank" rel="noopener">{e(item["name"])}</a></li>'
            for item in source_section["items"]
        )
        sections.append(
            f'<div class="sources-section"><h4><i data-lucide="{e(source_section["icon"])}"></i> '
            f'{e(source_section["title"])}</h4><ul>{links}</ul></div>'
        )
    return "\n".join(sections)


def render_nav(report: dict) -> str:
    links = []
    for section in report.get("sections", []):
        meta = section_meta(section)
        if section.get("articles"):
            links.append(f'<a href="#{e(meta["id"])}"><i data-lucide="{e(meta["icon"])}"></i> {e(meta["title"])}</a>')
    links.append('<a href="#sources"><i data-lucide="paperclip"></i> Sources</a>')
    return "\n".join(links)


def render_report(report: dict, dates: dict) -> str:
    sections = [render_section(section) for section in report.get("sections", [])]
    sections_html = "\n".join(section for section in sections if section)
    section_count = sum(1 for section in report.get("sections", []) if section.get("articles"))
    source_count = sum(len(source["items"]) for source in collect_sources(report))
    articles_count = sum(len(section.get("articles", [])) for section in report.get("sections", []))
    reviewed = report.get("articles_reviewed") or articles_count
    tagline = report.get("tagline") or "Everything you need to know from the last 24 hours."
    breaking = ""
    if report.get("breaking"):
        breaking = (
            f'<div class="breaking-banner" role="alert">'
            f'<span class="breaking-tag"><i data-lucide="zap"></i> BREAKING</span>{e(report["breaking"])}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(report.get("title") or "AI Daily")} — {e(dates["date_long"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<style>{REPORT_CSS}</style>
</head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <div class="masthead-brand">
      <span class="masthead-title">{e(report.get("title") or "AI Daily")}</span>
      <span class="masthead-edition">{e(dates["date_short"])}</span>
    </div>
    <nav class="masthead-nav">{render_nav(report)}</nav>
    <span class="masthead-version">Structured</span>
  </div>
</header>
<div class="hero-header">
  <div class="hero-inner">
    <div class="hero-date">{e(dates["day"])}, {e(dates["date_long"])} · Morning Edition</div>
    <h1 class="hero-title">AI Daily — <span>Your Morning</span><br>AI Briefing</h1>
    <p class="hero-tagline">{e(tagline)}</p>
    <div class="hero-stats">
      <div class="hero-stat-item"><span class="hero-stat-num">{e(reviewed)}</span><span class="hero-stat-label">articles reviewed</span></div>
      <div class="hero-stat-item"><span class="hero-stat-num">{section_count}</span><span class="hero-stat-label">topic sections</span></div>
      <div class="hero-stat-item"><span class="hero-stat-num">{source_count}</span><span class="hero-stat-label">verified sources</span></div>
    </div>
  </div>
</div>
<div class="page-wrapper">
  {breaking}
  {sections_html}
  <footer class="report-footer" id="sources">
    <h3 class="footer-title"><i data-lucide="paperclip"></i> All report sources</h3>
    <div class="sources-grid">{render_sources(report)}</div>
    <div class="footer-meta">
      <p><i data-lucide="cpu"></i> Generated: {e(dates["datetime"])} by AI Daily structured renderer</p>
      <p><i data-lucide="clock"></i> Time window: last 24 hours</p>
      <p><i data-lucide="bar-chart-2"></i> Sources analyzed: {source_count}</p>
      <p><i data-lucide="file-text"></i> Output: JSON content rendered to HTML</p>
    </div>
  </footer>
</div>
<script>lucide.createIcons();</script>
</body>
</html>"""


def rebuild_index(outputs_dir: Path) -> None:
    reports = sorted(outputs_dir.glob("AI_Daily_*.html"), reverse=True)
    items = "\n".join(
        f'    <li><a href="outputs/{r.name}">'
        f'<span class="date">{r.stem.replace("AI_Daily_", "")}</span>'
        f'<span class="label">AI Daily Brief</span></a></li>'
        for r in reports
    )
    if not items:
        items = '    <li style="color:#6B7280;padding:14px">No reports generated yet.</li>'

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Daily — Archive</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #F3F4F6; color: #111827; margin: 0; padding: 40px 16px; }}
  .container {{ max-width: 640px; margin: 0 auto; }}
  h1 {{ font-size: 28px; font-weight: 800; letter-spacing: -.03em; margin-bottom: 8px; }}
  p.sub {{ color: #6B7280; font-size: 14px; margin-bottom: 32px; }}
  ul {{ list-style: none; display: flex; flex-direction: column; gap: 10px; padding: 0; }}
  li a {{ display: flex; align-items: center; gap: 16px; background: #fff; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 18px; text-decoration: none; color: inherit; transition: box-shadow .15s; }}
  li a:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,.08); }}
  .date {{ font-size: 13px; font-weight: 700; color: #2563EB; font-variant-numeric: tabular-nums; }}
  .label {{ font-size: 14px; font-weight: 500; color: #374151; }}
</style>
</head>
<body>
<div class="container">
  <h1>AI Daily</h1>
  <p class="sub">Daily news briefing — generated automatically every morning.</p>
  <ul>
{items}
  </ul>
</div>
</body>
</html>"""

    Path("index.html").write_text(html_doc, encoding="utf-8")
    print("updated index.html")


def main() -> None:
    dates = get_date_info()
    print(f"generating AI Daily Brief for {dates['date']}...")

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    output_path = outputs_dir / f"AI_Daily_{dates['date']}.html"
    if output_path.exists():
        print(f"report already exists: {output_path} — skipping generation")
    else:
        report = run_agent(dates)
        output_path.write_text(render_report(report, dates), encoding="utf-8")
        print(f"saved {output_path}")

    rebuild_index(outputs_dir)


if __name__ == "__main__":
    main()
