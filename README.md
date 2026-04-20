# SoMeliaR 🍷

Sistema de gestión de bodega con IA para Meliá Hotels International.

Desarrollado por **Fernando Vilas Paz**.

---

## Qué es

Aplicación web Django para la gestión integral de la bodega de un hotel: inventario de vinos, control de stock, pedidos a proveedores, análisis de reposición con IA y anotaciones del sumiller.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django 5.2 |
| Base de datos | SQLite (desarrollo) |
| Frontend | Bootstrap 5.3 + HTMX |
| IA | Google Gemini 2.5 Flash |
| Media storage | Cloudinary |
| Servidor | Gunicorn + Render |
| Estáticos | WhiteNoise |

---

## Estructura del proyecto

```
SoMeliaR/
├── config/          # Settings, URLs raíz, WSGI
├── core/            # Dashboard, perfil, anotaciones, herramientas
├── bodega/          # Vinos, movimientos, stock
├── pedidos/         # Pedidos, líneas, análisis IA
├── proveedores/     # Proveedores y relación con vinos
├── templates/       # Templates HTML
├── static/          # CSS, JS, imágenes
└── media/           # Archivos subidos (local; Cloudinary en producción)
```

---

## Variables de entorno

| Variable | Descripción | Obligatoria en prod |
|---|---|---|
| `SECRET_KEY` | Clave secreta Django | Sí |
| `DEBUG` | `False` en producción | Sí |
| `GEMINI_API_KEY` | Clave API Google AI Studio | Sí |
| `CLOUDINARY_URL` | `cloudinary://key:secret@cloud_name` | Sí |

---

## Instalación local

```bash
# Clonar y entrar
git clone https://github.com/fvilpaz/SoMeliaR.git
cd SoMeliaR

# Entorno virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Dependencias
pip install -r requirements.txt

# Base de datos
python manage.py migrate

# Superusuario
python manage.py createsuperuser

# Servidor de desarrollo
python manage.py runserver
```

---

## Despliegue en Render

1. Conectar repositorio GitHub en [render.com](https://render.com)
2. Tipo de servicio: **Web Service**
3. Build command: `./build.sh`
4. Start command: `gunicorn config.wsgi:application`
5. Añadir variables de entorno: `SECRET_KEY`, `DEBUG=False`, `GEMINI_API_KEY`, `CLOUDINARY_URL`

> **Importante:** `CLOUDINARY_URL` es necesaria para que las imágenes (logos, avatares, fotos de vinos) persistan entre despliegues. Sin ella, Render borra los archivos al reiniciar el contenedor.

---

## Importar datos iniciales

Desde **Herramientas → Importar desde Excel**, sube el Libro de Bodega en formato `.xls` o `.xlsx`. El sistema importa automáticamente vinos, proveedores y stock inicial.

---

## Permisos de usuario

| Rol | Acceso |
|---|---|
| Usuario normal | Bodega, pedidos, anotaciones, perfil |
| Superusuario | Todo lo anterior + Herramientas (importar, logos, limpiar BD) |

---

## Licencia

Proyecto privado — Meliá Hotels International / Fernando Vilas Paz.
