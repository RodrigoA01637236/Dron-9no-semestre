# web/ — sitio público (Netlify)

Página pública del proyecto, publicada en Netlify. Son archivos estáticos: no necesita servidor
propio ni la laptop encendida.

Todo está en una sola página, `index.html`, pensada para productores (palabras sencillas, poco texto):

| Parte | Qué hace |
| --- | --- |
| Revisar una hoja | Toma o elige una foto y el modelo `sigatoka_cls_v1.onnx` la revisa **en el navegador** (onnxruntime-web). La foto no sale del dispositivo. Dice qué tan seguro está (de 0 a 100), avisa si quedó casi en el límite y qué hacer. *Mandar al técnico* comparte la foto con el resultado escrito encima (en la computadora: WhatsApp Web, la foto en Descargas y en el portapapeles) |
| Mapa del lote | Primero pregunta si el técnico mandó el mapa (`.geojson` de la estación) o si se quiere ver un ejemplo. Muestra cuadros de 20 × 20 m y qué revisar primero. El archivo se lee **en el navegador**: no se sube a ningún lado |
| Dron en vivo | Video, GPS y revisión en vivo de la Jetson (`jetson/zed_right.py`) a través de un túnel https |

En la computadora el resultado, el mapa y el dron se abren en grande junto a la portada; en el celular
salen en hojas que suben desde abajo. `motor.js` hace el trabajo (modelo, mapa, dron) y `index.html`
lo pinta. `identificar.html`, `mapa.html` y `dron.html` solo redirigen a la página principal para
que los enlaces viejos sigan sirviendo (`dron.html?dron=https://...` incluido).

Letra Geist (Google Fonts); sin internet usa la letra del sistema. `preparar.sh` copia a `web/` el
modelo (`vision/models/`) y Leaflet (`ui/static/leaflet/`), y baja onnxruntime-web 1.30.0 a
`web/vendor/` (verifica el sha256), así que no hay copias en git: Netlify lo corre en cada despliegue
(`netlify.toml` en la raíz). En el celular el modelo (unos 20 MB) se baja con la primera foto, o al
abrir la página si hay WiFi.

**Sin internet:** la Jetson sirve este mismo sitio por su hotspot con `jetson/sitio_local.sh`
(`http://10.42.0.1:8000`); ahí *Dron en vivo* se conecta solo a la cámara. Ver `jetson/README.md`,
sección *Página sin internet*.

## Probar en la computadora

```bash
bash web/preparar.sh
python3 -m http.server 8090 --directory web
# http://localhost:8090
```

## Publicar

Se publica con el CLI de Netlify desde la raíz del repo (`netlify deploy --prod`), o conectando el
repo en Netlify (*Project configuration > Build & deploy*) para que cada push a `main` se publique
solo; `netlify.toml` ya tiene el comando y la carpeta.

## Revisar una hoja en el navegador

- Mismo preprocesado que `vision/clasificador.py`: estirar a 384 × 384, RGB, /255, CHW.
- El navegador reduce la foto con otro algoritmo que OpenCV; en las pruebas la diferencia fue de
  1 a 2 puntos de probabilidad (`bus.jpg`: 53 % contra 54 % Sigatoka).
- Usa `ort.wasm.min.js` (solo WebAssembly, ~14 MB de `.wasm`, unos 4 MB comprimido); la primera
  visita lo baja y luego queda en caché.

## Mapa

- El sitio no guarda ubicaciones del cultivo: el mapa solo existe en el archivo que se abre. Así nada
  de dónde está el lote o dónde hay enfermedad queda publicado.
- El archivo sale de la estación: **Mapa > Descargar el mapa** (`/api/geojson`). Trae, por foto, la
  ubicación, el diagnóstico, si lo revisó alguien y si el modelo no estaba seguro. Archivos de antes
  (sin `clave`, `color` ni `dudoso`) también abren: la página lo deduce del nombre y la confianza.
- Dos vistas: *Cuadros* (la condición que más se repite en cada cuadro de 20 m; empate gana la más
  grave; borde rojo punteado si el cuadro tiene alguna foto con Sigatoka) y *Cada foto*.
- El lote del archivo se ve sobre el fondo satelital (Esri), que sí pide mosaicos a internet; el
  ejemplo no usa fondo.

## Dron en vivo

La página es `https://` y la Jetson da `http://<ip>:8080` en la red local: el navegador no deja
mezclar las dos. Para verla desde aquí, en la Jetson (con `zed_right.py` ya corriendo):

```bash
# una sola vez
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
# cada vez
cloudflared tunnel --url http://localhost:8080
```

Imprime `https://<palabras>.trycloudflare.com`: esa dirección se escribe en *Dron en vivo*
(o se comparte como `https://dron-sigatoka.netlify.app/?dron=https://...`). El túnel no toca la cámara; solo publica la
página del puerto 8080. Quien tenga la dirección puede ver el video y tomar fotos, así que
compártela solo con el equipo. La dirección cambia cada vez y se cierra con la terminal.
