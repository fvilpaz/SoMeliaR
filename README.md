<div align="right">
  <img src="https://img.shields.io/badge/EN-1a6fc4?style=flat-square" alt="English">
  &nbsp;<a href="README.es.md"><img src="https://img.shields.io/badge/ES-555555?style=flat-square" alt="Español"></a>
</div>

# SoMeliaR 🍷

AI-powered cellar management system for Meliá Hotels International.

Developed by **Fernando Vilas Paz**.

---

## What it is

Django web application for comprehensive hotel cellar management: wine inventory, stock control, supplier orders, AI-powered restocking analysis, and sommelier notes.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 |
| Database | SQLite (development) |
| Frontend | Bootstrap 5.3 + HTMX |
| AI | Google Gemini 2.5 Flash |
| Media storage | Cloudinary |
| Server | Gunicorn + Render |
| Static files | WhiteNoise |

---

## Project structure

```
SoMeliaR/
├── config/          # Settings, root URLs, WSGI
├── core/            # Dashboard, profile, notes, tools
├── bodega/          # Wines, movements, stock
├── pedidos/         # Orders, lines, AI analysis
├── proveedores/     # Suppliers and their relationship with wines
├── templates/       # HTML templates
├── static/          # CSS, JS, images
└── media/           # Uploaded files (local; Cloudinary in production)
```

---

## Environment variables

| Variable | Description | Required in prod |
|---|---|---|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | `False` in production | Yes |
| `GEMINI_API_KEY` | Google AI Studio API key | Yes |
| `CLOUDINARY_URL` | `cloudinary://key:secret@cloud_name` | Yes |

---

## Local installation

```bash
# Clone and enter
git clone https://github.com/fvilpaz/SoMeliaR.git
cd SoMeliaR

# Virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Database
python manage.py migrate

# Superuser
python manage.py createsuperuser

# Development server
python manage.py runserver
```

---

## Deployment on Render

1. Connect the GitHub repository on [render.com](https://render.com)
2. Service type: **Web Service**
3. Build command: `./build.sh`
4. Start command: `gunicorn config.wsgi:application`
5. Add environment variables: `SECRET_KEY`, `DEBUG=False`, `GEMINI_API_KEY`, `CLOUDINARY_URL`

> **Important:** `CLOUDINARY_URL` is required so that images (logos, avatars, wine photos) persist between deployments. Without it, Render deletes files when the container restarts.

---

## Importing initial data

From **Tools → Import from Excel**, upload the Cellar Book in `.xls` or `.xlsx` format. The system automatically imports wines, suppliers, and initial stock.

---

## User permissions

| Role | Access |
|---|---|
| Regular user | Cellar, orders, notes, profile |
| Superuser | All of the above + Tools (import, logos, clear DB) |

---

## License

Private project — Meliá Hotels International / Fernando Vilas Paz.
