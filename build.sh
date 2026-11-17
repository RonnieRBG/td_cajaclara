#!/usr/bin/env bash
# Pasos de construcción al publicar (Render, Railway u otro servicio):
# instala dependencias y junta los archivos estáticos.
# No ejecuta migraciones: en Neon las tablas de datos son del equipo de datos
# (ver ACOPLAMIENTO.md, paso 1.4).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
