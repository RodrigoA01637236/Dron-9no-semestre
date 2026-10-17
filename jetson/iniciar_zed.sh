#!/bin/bash
# Lanzador de ejemplo, reproducido de los comandos del proyecto.
# Inicia la ventana solo dentro de una sesión gráfica de Ubuntu.
LOG="/home/jetsonnanoorin/ZED_Pruebas/zed-right.log"
PYTHON="/home/jetsonnanoorin/ZED_Pruebas/.venv/bin/python"
SCRIPT="/home/jetsonnanoorin/ZED_Pruebas/zed_right.py"

exec 9>/tmp/zed-right.lock
flock -n 9 || exit 0

sleep 30
cd /home/jetsonnanoorin/ZED_Pruebas || exit 1
echo "===== INICIO ZED $(date) =====" >> "$LOG"

while true; do
    echo "Intentando abrir ZED..." >> "$LOG"
    "$PYTHON" "$SCRIPT" >> "$LOG" 2>&1
    RESULTADO=$?
    if [ "$RESULTADO" -eq 0 ]; then
        echo "ZED cerrada normalmente" >> "$LOG"
        break
    fi
    echo "Error ZED ($RESULTADO). Reintentando en 10 segundos..." >> "$LOG"
    sleep 10
done
