# xakker-org-backend

Django REST API for the Xakker platform (auth, courses, admin). Serves only `/api/*` and `/admin/*` — no HTML pages. The frontend (landing + React app) lives in a separate repo: [xakker-org-frontend](https://github.com/xakker-org/xakker-org-frontend).

## Local setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in SECRET_KEY, DB credentials
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

API available at `http://localhost:8000/api/`, admin at `http://localhost:8000/admin/`.

## Docker

```bash
docker build -t xakker-backend .
docker run --env-file .env -p 8000:8000 -e PORT=8000 xakker-backend
```

Or with Postgres included: `docker compose up --build` (uses `docker-compose.yml`, reads `.env`).

## Deploy (Render)

`render.yaml` provisions a Docker web service + managed Postgres. Set `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` to match wherever the frontend is deployed.
