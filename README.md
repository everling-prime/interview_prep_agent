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
├── models/
│   └── data_models.py
├── output/
│   └── prep_reports/        # .gitignored except .gitkeep
├── config.py
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

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
- `FIRECRAWL_API_KEY` – Reserved for future crawling, currently required by Config

## Usage

Run the agent from the repo root:

```bash
uv run python main.py --company stripe.com --user-id your@email.com
```

Common flags:

- `--debug` – verbose logs
- `--email-only` – skip web scraping
- `--save-to-docs` – create a Google Doc via Arcade
- `--docs-only` – only save to Google Docs (no local file)
- `--output-dir PATH` – change local output directory (default: `output/prep_reports`)

Examples:

```bash
uv run python main.py --company openai.com --user-id you@example.com --debug
uv run python main.py --company stripe.com --user-id you@example.com --save-to-docs
```

## Notes on web research

- The web researcher attempts at most 5 URLs per domain and caps at 5 successful scrapes, prioritizing common pages like `/about`, `/company`, `/mission`, etc.
- Pages returning 404s are skipped gracefully; scraping continues until the cap is hit.

## Output

- Local reports are written to `output/prep_reports/<company>_prep_<timestamp>.md`.
- When `--save-to-docs` is set, a Google Doc is created via Arcade and the URL is printed.

## Development

- Archived, non-critical or experimental files are stored in `archive_unused/` (git-ignored) so they don’t pollute the repo.
- `output/` contents are ignored by git, except for `.gitkeep` placeholders.
- Keep `uv.lock` committed for deterministic installs.

## Troubleshooting

- Import errors: ensure you run from the repository root and that `uv sync` (or `pip install`) completed successfully.
- Missing keys: `config.py` requires `ARCADE_API_KEY`, `OPENAI_API_KEY`, and `FIRECRAWL_API_KEY`.
- Google Docs failures: verify Arcade auth in the console logs and that your account has Drive access.