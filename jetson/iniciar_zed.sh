#!/bin/bash
# Lanzador: abre zed_right.py y lo vuelve a abrir si se cae.
# Lo arranca el autostart de la sesión gráfica (ver jetson/README.md).
# Para cerrarlo sin que se vuelva a abrir: bash jetson/zed_control.sh detener
CARPETA="$HOME/ZED_Pruebas"
LOG="$CARPETA/zed-right.log"
PYTHON="$CARPETA/.venv/bin/python"
PAUSA="$CARPETA/PAUSA"   # si existe este archivo, no se abre ni se reabre

# La versión del repo (se actualiza con git pull); si no está, la copia de ZED_Pruebas.
SCRIPT="$HOME/Dron-9no-semestre/jetson/zed_right.py"
[ -f "$SCRIPT" ] || SCRIPT="$CARPETA/zed_right.py"

[ -f "$PAUSA" ] && exit 0

exec 9>/tmp/zed-right.lock
flock -n 9 || exit 0

sleep "${ESPERA:-30}"
cd "$CARPETA" || exit 1
echo "===== INICIO ZED $(date) =====" >> "$LOG"

while [ ! -f "$PAUSA" ]; do
    echo "Intentando abrir ZED ($SCRIPT)..." >> "$LOG"
    "$PYTHON" "$SCRIPT" >> "$LOG" 2>&1
    RESULTADO=$?
    if [ "$RESULTADO" -eq 0 ]; then
        echo "ZED cerrada normalmente" >> "$LOG"
        break
    fi
    echo "Error ZED ($RESULTADO). Reintentando en 10 segundos..." >> "$LOG"
    sleep 10
done
