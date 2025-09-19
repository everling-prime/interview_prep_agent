# Interview Prep Agent

AI-powered agent that analyzes your email communications and researches a company’s website to generate an interview preparation report. Saves locally to `output/prep_reports/` and can optionally create a Google Doc via Arcade.

## Features

- Analyze Gmail threads for a target company domain
- Scrape up to 5 key pages from the company website
- Generate a tailored prep report using OpenAI
- Save locally and/or to Google Docs via Arcade

## Project structure

```
interview_prep_agent/
├── agents/
│   ├── email_analyzer.py
│   ├── web_researcher.py
│   └── prep_coach.py
│   └── discovery.py
├── models/
│   └── data_models.py
├── output/
│   └── prep_reports/        # .gitignored except .gitkeep
├── tools/
│   ├── gmail.py
│   ├── firecrawl.py
│   ├── search.py
│   └── executor.py
├── utils/
│   ├── logging.py
│   ├── validators.py
│   ├── auth.py
│   └── schema.py
├── config.py
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Architecture

- Agents:
  - `email_analyzer.py`: Gmail via Arcade + LLM JSON extraction to classify interview‑related emails and contacts.
  - `web_researcher.py`: Orchestrates discovery and scraping to get canonical company pages.
  - `discovery.py`: Merges Firecrawl site mapping + Google search, then uses an LLM to pick the best URLs (about/team/careers).
- Tools:
  - `gmail.py`, `firecrawl.py`, `search.py`: Thin wrappers over Arcade toolkits with uniform execution + logging via `executor.py`.
- Utils:
  - `logging.py`: Structured JSON logs with `run_id`, `step`, `tool`, `outcome`, `duration_ms` (+extra).
  - `validators.py`: URL/domain sanitation and normalization.
  - `auth.py`: Client factories for Arcade and OpenAI.
- Agent Loop:
  - Explicit perceive → decide → act (tool) → reflect → next, with structured logs at each step.

## Requirements

- Python 3.13+
- `uv` package manager (recommended) or `pip`

## Setup

1) Install dependencies

Using uv (recommended):

```bash
uv sync
```

Using pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r <(uv pip compile pyproject.toml)
```

2) Environment variables

Copy `.env.example` to `.env` and provide keys:

```bash
cp .env.example .env
```

Required variables loaded in `config.py`:

- `ARCADE_API_KEY` – Arcade API key (for Gmail/Google Docs tool access)
- `OPENAI_API_KEY` – OpenAI key for AI report generation

## Usage

Run the agent from the repo root:

```bash
uv run python main.py --company stripe.com --user-id your@email.com
```

Common flags:

- `--debug` – verbose logs
- `--email-only` – skip web scraping
- `--fast-web` – faster web discovery/scrape (fewer calls, no crawl fallback)
- `--save-to-docs` – create a Google Doc via Arcade
- `--docs-only` – only save to Google Docs (no local file)
- `--output-dir PATH` – change local output directory (default: `output/prep_reports`)

Examples:

```bash
uv run python main.py --company openai.com --user-id you@example.com --debug
uv run python main.py --company stripe.com --user-id you@example.com --save-to-docs
```

## Demo

- Quick run script: `bash scripts/demo.sh <company_domain> <user_email> [--debug] [--save-to-docs]`
- Examples:
  - `bash scripts/demo.sh arcade.dev you@example.com --debug`
  - `bash scripts/demo.sh stripe.com you@example.com --save-to-docs`
- Optional: make it executable and run directly: `chmod +x scripts/demo.sh && ./scripts/demo.sh arcade.dev you@example.com`

## Notes on web research

- Discovery combines Firecrawl site mapping and GoogleSearch to find canonical pages (about, team/leadership, careers).
- An LLM ranks and selects the best candidates, then we scrape via Firecrawl.ScrapeUrl (markdown).
- Debug mode and `--fast-web` keep calls minimal (1 map + 1 search; scrape up to 2 pages; no crawl fallback). Full mode maps + searches more broadly, and may use a tiny crawl fallback if needed.
- 404s and minor parsing issues are skipped gracefully; URLs are sanitized and normalized to HTTPS.

## Output

- Local reports are written to `output/prep_reports/<company>_prep_<timestamp>.md`.
- When `--save-to-docs` is set, a Google Doc is created via Arcade and the URL is printed.

## Development

- Archived, non-critical or experimental files are stored in `archive_unused/` (git-ignored) so they don’t pollute the repo.
- `output/` contents are ignored by git, except for `.gitkeep` placeholders.
- Keep `uv.lock` committed for deterministic installs.

## Troubleshooting

- Import errors: ensure you run from the repository root and that `uv sync` (or `pip install`) completed successfully.
- Missing keys: `config.py` requires `ARCADE_API_KEY` and `OPENAI_API_KEY`.
- Google Docs: the first run will prompt Arcade authorization in your terminal; approve once and retry.
