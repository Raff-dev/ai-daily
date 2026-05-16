# AI Daily Brief

An open-source, self-hosted AI news briefing that runs every morning automatically.
Claude searches the web for AI news from the last 24 hours, filters and verifies it,
and generates a polished HTML report — no server required.

**Live example:** `https://<your-username>.github.io/ai-daily`

---

## What it covers

- Developer tools (Claude, Copilot, Cursor, Codex…)
- Robotics & drones
- Defense & autonomous weapons
- Space & astronautics
- Startup funding rounds
- AI stock market moves *(only on significant events)*

---

## Setup — 3 steps

### 1. Fork this repo

Click **Fork** at the top of this page. Make sure the repo is **public** (required for free
GitHub Pages and Actions minutes).

### 2. Add your Anthropic API key

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | your key from [console.anthropic.com](https://console.anthropic.com) |

### 3. Enable GitHub Pages

Go to **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: `main` / `/ (root)`

Save. Your archive will be live at `https://<username>.github.io/<repo-name>/`.

That's it. The workflow runs daily at **05:00 UTC** (06:00 Warsaw CET / 07:00 CEST).
You can also trigger it manually from the **Actions** tab → **Daily AI Brief** → **Run workflow**.

---

## Run locally

```bash
git clone https://github.com/<you>/ai-daily
cd ai-daily
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python run.py
# opens outputs/AI_Daily_YYYY-MM-DD.html
```

---

## Configuration

| Env variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Override the Claude model used |

To change the schedule, edit the `cron` line in `.github/workflows/daily.yml`.
The cron format is UTC — use [crontab.guru](https://crontab.guru) to convert.

---

## Cost

Each run makes ~8 web searches and generates a long HTML document.
With the default `claude-sonnet-4-6` model, expect roughly **$0.05–0.15 per report**
depending on how much news there is. Monthly cost: ~$1.50–4.50.

---

## License

MIT — fork it, modify it, self-host it.
