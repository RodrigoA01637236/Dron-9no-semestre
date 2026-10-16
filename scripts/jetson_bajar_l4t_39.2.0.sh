#!/usr/bin/env bash
# Baja Jetson Linux de 39.2.1 a 39.2.0 con apt, para que coincida con el driver
# de la ZED Link Duo (stereolabs-zedlink-duo_1.4.4-...-L4T39.2.0). Sin reflashear.
#
# El repo de NVIDIA (jetson/som y jetson/common, rama r39.2) conserva las dos
# versiones. Todos los paquetes nvidia-l4t-* dependen de nvidia-l4t-core con
# versión exacta, así que se bajan TODOS juntos en una sola transacción.
#
# Uso (en la Jetson, desde la raíz del repo):
#   bash scripts/jetson_bajar_l4t_39.2.0.sh             # solo simula, no cambia nada
#   bash scripts/jetson_bajar_l4t_39.2.0.sh --aplicar   # hace el cambio (pide confirmar)
#
# Antes: respaldar data/ y lo que no esté en git. Si algo sale mal, la salida es
# el reflasheo de docs/decisiones/2026-10-16-camara-zedx-errores-csi.md.
set -euo pipefail

OBJETIVO="39.2.0-"
DRIVER_URL="https://download.stereolabs.com/drivers/zedx/1.4.4/R39.2/stereolabs-zedlink-duo_1.4.4-LI-MAX96712-L4T39.2.0_arm64.deb"
APLICAR=0
[[ "${1:-}" == "--aplicar" ]] && APLICAR=1

if ! grep -q "R39 (release), REVISION: 2.1" /etc/nv_tegra_release 2>/dev/null; then
  echo "Esta Jetson no está en L4T 39.2.1:"; head -1 /etc/nv_tegra_release 2>/dev/null || true
  echo "No hago nada."; exit 1
fi

echo "== Actualizando la lista de paquetes"
sudo apt-get update -qq

# Para cada paquete nvidia-l4t-* instalado, busca la versión 39.2.0 en el repo.
LISTA=(); SIN=()
while read -r pkg; do
  ver=$(apt-cache madison "$pkg" | awk -F'|' '{gsub(/ /,"",$2); print $2}' | grep -F "$OBJETIVO" | head -1 || true)
  if [[ -n "$ver" ]]; then LISTA+=("$pkg=$ver"); else SIN+=("$pkg"); fi
done < <(dpkg-query -W -f='${Status} ${Package}\n' 'nvidia-l4t-*' 2>/dev/null | awk '$3=="installed"{print $4}')

echo "== Se bajarán ${#LISTA[@]} paquetes a 39.2.0"
[[ ${#SIN[@]} -gt 0 ]] && echo "   Sin versión 39.2.0 (se quedan igual): ${SIN[*]}"

echo "== Simulación (no cambia nada)"
SIM=$(apt-get -s install --allow-downgrades "${LISTA[@]}" 2>&1) || { echo "$SIM"; echo "La simulación falló; no sigo."; exit 1; }
echo "$SIM" | grep -E "^(Inst|Remv)" | sed 's/^/   /' | head -100
if echo "$SIM" | grep -q "^Remv"; then
  echo "ALTO: apt quiere QUITAR paquetes (líneas Remv). Manda esta salida antes de seguir."
  exit 1
fi

if [[ $APLICAR -eq 0 ]]; then
  echo; echo "Todo se ve bien. Para hacerlo de verdad: bash $0 --aplicar"; exit 0
fi

read -r -p "¿Bajar a 39.2.0 ahora? Escribe SI para continuar: " r
[[ "$r" == "SI" ]] || { echo "Cancelado."; exit 1; }

sudo apt-get install -y --allow-downgrades "${LISTA[@]}"
# Que apt upgrade no la vuelva a subir a 39.2.1.
sudo apt-mark hold "${LISTA[@]%%=*}"

echo "== Reinstalando el driver de la ZED Link Duo (los paquetes del kernel reescriben DTB/extlinux)"
DEB="/tmp/$(basename "$DRIVER_URL")"
[[ -f "$DEB" ]] || wget -q -O "$DEB" "$DRIVER_URL"
sudo dpkg -i "$DEB"

cat <<'FIN'

Listo. Ahora:
  1. sudo shutdown -h now   (apagado completo, NO reboot)
  2. Desconecta Jetson y ZED Link 30 s y vuelve a encender.
     El primer arranque puede tardar más porque actualiza el firmware de arranque:
     no lo desconectes hasta que aparezca el escritorio.
  3. Verifica:
       head -1 /etc/nv_tegra_release        # REVISION: 2.0
       gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=60 ! fakesink
       sudo journalctl -u nvargus-daemon -b --no-pager | grep -c CRC   # 0
       /usr/local/zed/tools/ZED_Explorer
Para deshacer el bloqueo más adelante: sudo apt-mark unhold $(apt-mark showhold)
FIN
