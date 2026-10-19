#!/bin/bash
# Controla el programa de la cámara (zed_right.py) y su lanzador que lo reabre.
#
#   bash jetson/zed_control.sh detener    cierra la cámara y NO deja que se reabra
#                                         (ni al reiniciar la Jetson) hasta "iniciar"
#   bash jetson/zed_control.sh iniciar    la vuelve a abrir, con video y modelo
#   bash jetson/zed_control.sh reiniciar  detener + iniciar (por ejemplo después de git pull)
#   bash jetson/zed_control.sh estado     qué está corriendo, dirección web y últimas líneas
#   bash jetson/zed_control.sh instalar   copia el lanzador nuevo a ~/ZED_Pruebas (una vez)
CARPETA="$HOME/ZED_Pruebas"
LOG="$CARPETA/zed-right.log"
AQUI="$(cd "$(dirname "$0")" && pwd)"
# Patrones anclados al inicio del comando para no atrapar terminales que solo mencionan los nombres.
LANZADOR='^[^ ]*bash [^ ]*iniciar_zed\.sh'
PROGRAMA='^[^ ]*python[0-9.]* [^ ]*zed_right\.py'
OTROS='^[^ ]*ZED_(Studio|Explorer)'

estado() {
    echo "== Corriendo:"
    pgrep -af "$LANZADOR|$PROGRAMA|$OTROS" || echo "   nada"
    [ -f "$CARPETA/PAUSA" ] && echo "== En pausa: no se abrirá hasta 'bash $0 iniciar'"
    if [ -f "$LOG" ]; then
        echo "== Dirección para la estación:"
        grep "\[WEB\]" "$LOG" | tail -n 2
        echo "== Últimas líneas de $LOG:"
        tail -n 12 "$LOG"
    fi
}

detener() {
    mkdir -p "$CARPETA"
    touch "$CARPETA/PAUSA"
    pkill -f "$LANZADOR"
    pkill -f "$PROGRAMA"
    for _ in $(seq 10); do
        pgrep -f "$PROGRAMA" >/dev/null || break
        sleep 1
    done
    pkill -9 -f "$PROGRAMA" 2>/dev/null
    echo "Cámara cerrada. No se volverá a abrir sola hasta: bash $0 iniciar"
}

iniciar() {
    rm -f "$CARPETA/PAUSA"
    if pgrep -f "$LANZADOR" >/dev/null; then
        echo "Ya estaba corriendo."
    else
        ESPERA=0 nohup "$CARPETA/iniciar_zed.sh" >/dev/null 2>&1 &
        echo "Abriendo la cámara (tarda unos segundos)..."
        sleep 10
    fi
    estado
}

case "$1" in
    detener)   detener ;;
    iniciar)   iniciar ;;
    reiniciar) detener; rm -f "$CARPETA/PAUSA"; sleep 2; iniciar ;;
    estado)    estado ;;
    instalar)
        mkdir -p "$CARPETA"
        if [ -f "$CARPETA/iniciar_zed.sh" ]; then
            cp "$CARPETA/iniciar_zed.sh" "$CARPETA/iniciar_zed.sh.respaldo-$(date +%Y%m%d-%H%M%S)"
            echo "Respaldo del lanzador anterior en $CARPETA/iniciar_zed.sh.respaldo-*"
        fi
        cp "$AQUI/iniciar_zed.sh" "$CARPETA/iniciar_zed.sh"
        chmod +x "$CARPETA/iniciar_zed.sh"
        echo "Lanzador instalado en $CARPETA/iniciar_zed.sh (usa jetson/zed_right.py del repo)."
        ;;
    *)
        sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
        exit 1
        ;;
esac
