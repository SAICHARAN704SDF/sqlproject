# EscapeStress

Small Flask app that provides a calm companion for mental wellness: chat-based check-ins, breathing exercises, journaling, and a music section.

## Quick start

1. Create a virtual environment and activate it (macOS / Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the project's checks (quick sanity):

```bash
python3 run_checks.py
```

4. Start the app locally:

```bash
python3 app.py
```

The app will start on http://127.0.0.1:5000 by default.

## Notes for pushing to GitHub

- This repository contains a simple Flask app and a lightweight model file under `model/` (not tracked here). If you plan to push the model file to GitHub, ensure it's small enough or use Git LFS.
- The included GitHub Actions workflow runs `python3 run_checks.py` on push to `main`.

## Project layout

- `app.py` — Flask app and routes
- `templates/` — Jinja2 templates for pages
- `static/` — client assets (CSS / JS / images)
- `model/` — serialized ML model used by the app
- `run_checks.py` — simple integration checks used by CI

If you want additional CI steps, tests, or a deployment guide, tell me which provider (Heroku, Vercel, Railway, etc.) and I’ll add the steps.
