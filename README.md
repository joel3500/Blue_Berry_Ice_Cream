# Blue Berry Ice Cream — Deployment Guide (GitHub + Render)

This repo contains a Flask app under `Blue_Berry_Ice_Cream/` with Jinja templates and static assets.

## 3) Test locally (optional)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd Blue_Berry_Ice_Cream
gunicorn -w 2 -b 0.0.0.0:8000 products:products
# open http://localhost:8000
```

## 5) Deploy on Render
- Dashboard → **New +** → **Web Service** → **Build with Blueprint** → Select your repo.
- Render will read `render.yaml`.
- Confirm the service; first deploy may take a minute.
- After deploy, open the service URL.

### Notes about SQLite writes
If your app needs to **write** to `blue_blerry_ice_cream.db`, configure a **Disk** in `render.yaml` (see commented section) and point your app to a path on that disk (e.g., `/opt/render/project/src/data/app.db`). You can pass this path via an env var (e.g., `DB_PATH`) and read it in `products.py`.

## 6) Common gotchas
- Start command must target the Flask object: `products:products`.
- `rootDir` must be the folder that contains `products.py`, `templates/`, `static/`.
- Do **not** commit large local environments or caches.
- If images don’t show online, ensure they live under `Blue_Berry_Ice_Cream/static/` and URLs in templates use `url_for('static', filename='...')`.