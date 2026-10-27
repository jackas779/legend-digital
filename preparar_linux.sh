#!/usr/bin/env bash
# ============================================================
#  Preparación en una máquina nueva (Linux/macOS).
#  Paso previo único: instalar dependencias con pip.
#  Todo lo demás lo hace un solo comando: manage.py preparar
# ============================================================
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
fi

.venv/bin/python -m pip install -r back/requirements.txt

.venv/bin/python manage.py preparar

echo
echo "  Para levantar el servidor:"
echo "    .venv/bin/python manage.py runserver"
