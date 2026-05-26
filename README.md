# PDF Fact Checker

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

A Streamlit app that extracts verifiable claims from uploaded PDFs and fact-checks each one against the live web using Groq's LLM with built-in browser search. Results stream in real time as each claim is verified.

## Features

- PDF text extraction via PyMuPDF (no external services)
- Automatic claim detection — stats, dates, financial figures, technical specs
- Real-time web-grounded fact verification via Groq (`openai/gpt-oss-120b` + `browser_search`)
- Live streaming UI — verdict cards appear as each claim finishes, not after all are done
- Color-coded results: green (Verified), amber (Inaccurate), red (Unverified)
- Live summary counter updated after each verdict
- JSON export of all results

## Local Setup

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed
- A [Groq API key](https://console.groq.com)

### Install and run

```bash
uv sync
```

Add your API key to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_..."
```

```bash
uv run streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this repository to GitHub. Make sure `.streamlit/secrets.toml` is listed in `.gitignore` — **never commit your API key**.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Connect your GitHub repo and set the **Main file path** to `app.py`.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
5. Click **Deploy**. Streamlit Cloud will install dependencies from `requirements.txt` automatically.

> Update the badge URL at the top of this file with your actual app URL after the first deploy.

## Regenerating requirements.txt

Run this whenever you change dependencies in `pyproject.toml`:

```bash
uv pip compile pyproject.toml -o requirements.txt
```

Streamlit Cloud reads `requirements.txt` at deploy time; it does not run `uv sync`.
