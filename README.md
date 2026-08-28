# Project Simulation Website

The production Flask portfolio for [Project Simulation](https://github.com/AX028/project-simulation).
It explains the framework, displays cached public GitHub activity, and delivers contact requests
by email without storing submissions.

> The source is publicly viewable. No license has been granted yet.

## Local development

Requires Python 3.11 or newer.

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[dev]"
flask --app app run --debug
```

The homepage and `/api/projects` remain usable if GitHub is unavailable. The contact form shows a
safe delivery error until SMTP is configured.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Production | Session and CSRF signing |
| `CONTACT_RECIPIENT` | Contact | Destination mailbox |
| `CONTACT_SENDER` | Contact | Verified sender address |
| `SMTP_HOST`, `SMTP_PORT` | Contact | SMTP endpoint |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Provider-dependent | SMTP authentication |
| `SMTP_USE_TLS` | No | Defaults to `true` |
| `GITHUB_TOKEN` | No | Raises GitHub API rate limits |
| `CACHE_TTL_SECONDS` | No | GitHub cache lifetime; defaults to 600 |

Never commit real credentials. Contact names, addresses, subjects, and message bodies are held only
for the duration of the request and are not written to application logs or a database.

## Routes

- `GET /` — portfolio and contact form
- `POST /contact` — validated, CSRF-protected, rate-limited email delivery
- `GET /healthz` — Render health check
- `GET /api/projects` — sanitized cached repository metadata

## Verification

```bash
pytest
ruff check .
mypy project_website
```

## Render deployment

`render.yaml` defines the Python service, Gunicorn command, health path, and non-secret defaults.
Create a Blueprint from this repository, then provide the required secrets in Render. Do not place
secret values in the Blueprint file. Once deployed and smoke-tested, set the repository homepage
to the Render URL instead of the obsolete GitHub Pages URL.

