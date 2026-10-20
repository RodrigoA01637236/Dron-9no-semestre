# web/ — sitio público (Netlify)

Página pública del proyecto, publicada en Netlify. Son archivos estáticos: no necesita servidor
propio ni la laptop encendida.

| Página | Qué hace |
| --- | --- |
| `index.html` | Qué es el Dron Sigatoka, cómo funciona y qué tan bueno es el modelo |
| `identificar.html` | Sube o toma una foto de una hoja y el modelo `sigatoka_cls_v1.onnx` la diagnostica **en el navegador** (onnxruntime-web). La foto no sale del dispositivo |
| `dron.html` | Video, GPS y diagnóstico en vivo de la Jetson (`jetson/zed_right.py`) a través de un túnel https |

El estilo sigue [DESIGN.md](../DESIGN.md) (mismos colores, Manrope y componentes que la estación).
`preparar.sh` copia a `web/` el modelo (`vision/models/`) y la fuente (`ui/static/fuentes/`), y baja
onnxruntime-web 1.30.0 a `web/vendor/` (verifica el sha256), así que no hay copias en git y el sitio
no depende de ningún CDN: Netlify lo corre en cada despliegue (`netlify.toml` en la raíz).

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

## Identificar en el navegador

- Mismo preprocesado que `vision/clasificador.py`: estirar a 384 × 384, RGB, /255, CHW.
- El navegador reduce la foto con otro algoritmo que OpenCV; en las pruebas la diferencia fue de
  1 a 2 puntos de probabilidad (`bus.jpg`: 53 % contra 54 % Sigatoka).
- Usa `ort.wasm.min.js` (solo WebAssembly, ~14 MB de `.wasm`, unos 4 MB comprimido); la primera
  visita lo baja y luego queda en caché.

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
(o se comparte como `dron.html?dron=https://...`). El túnel no toca la cámara; solo publica la
página del puerto 8080. Quien tenga la dirección puede ver el video y tomar fotos, así que
compártela solo con el equipo. La dirección cambia cada vez y se cierra con la terminal.
