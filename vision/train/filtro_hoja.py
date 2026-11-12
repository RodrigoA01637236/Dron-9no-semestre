"""Entrena el filtro "¿esto es hoja de plátano?" y lo guarda en el JSON del modelo (filtro_hoja).

Por qué hace falta: la clase "sin_hoja" se entrenó con otras plantas, frutos y fondos de
cultivo. Una foto de una mesa, una mano, una taza o una pared nunca la vio, y ante eso el
modelo elige una clase de hoja (casi siempre "otra condición") con mucha seguridad.

Qué hace:
1. Corta cada foto en cuadros igual que la inferencia (vision/parches.py) y saca los rasgos
   de cada cuadro con el mismo modelo (vision/rasgos.py: 1280 números de la penúltima capa).
2. Positivos: los cuadros de las fotos de hoja (--hojas) que el modelo lee como hoja de
   plátano. Las subcarpetas con el nombre de una clase de `ignorar` (sin_hoja) se saltan.
   Negativos: todos los cuadros de las fotos de objetos (--objetos, --coco) y, de cada una,
   un acercamiento simulado (un recorte del 30-60 % agrandado a 2016 x 1512 y algo
   desenfocado), que es lo que sale al apuntar el celular a algo de cerca.
3. Regresión logística con regularización L2 y clases equilibradas.
4. Un cuadro pasa si w · rasgos + b >= umbral (-3). Modo "foto": la foto cuenta como sin hoja
   solo si ninguno de sus cuadros de hoja pasa; si alguno pasa, el veredicto es el del modelo
   con todos sus cuadros. Así el filtro nunca le quita a una hoja los cuadros con manchas
   cafés, que son los de la Sigatoka.

   Cómo se eligió (dejando fuera una fuente de fotos de hoja a la vez, para medir fotos como
   las de un celular nuevo): de 3986 fotos de hoja de 10 fuentes, con -3 cambiaron 7 (0.2 %);
   de 760 fotos de objetos que el filtro no vio, el modelo leía 130 como hoja y el filtro atrapa
   47 de esas (de las casi sin verde, 27 de 56). Lo que se probó
   y salió peor: quitar cuadro por cuadro, o un umbral más estricto para cuadros o fotos con
   poco verde. Las lesiones cafés casi no tienen verde, y fuentes nuevas de fotos de Sigatoka
   perdían hasta 26 de 897 fotos (con la versión de un día antes, 8 de 122 fotos de prueba con
   Sigatoka salían "sin hoja"). Un umbral más alto (-2) atrapa más objetos pero cambia 30 fotos
   de hoja; uno más bajo (-4) casi no atrapa objetos.
   El reporte muestra los dos lados con el 20 % de las fotos apartado (al azar, así que de las
   mismas fuentes: es más optimista que dejar fuera una fuente).
5. Una segunda sonda para la foto completa reducida, que es lo que usa el video en vivo del
   dron (modo "imagen"): los rasgos de una imagen entera no se parecen a los de un cuadro.
   Umbral --umbral-imagen (-3). Dejando fuera una fuente a la vez cambiaron 4 de 4192 fotos de
   hoja (ninguna aérea) y los objetos que el video leía como hoja bajaron de 10 a 4 de 760. En
   ese modo el modelo ya rechaza casi todos los objetos solo, porque ve la escena completa.

--coco N baja N fotos al azar de COCO test2017 (escenas y objetos cotidianos, 160 KB cada una)
a data/raw/objetos_coco/. Hace falta internet una vez; después se reusan.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/filtro_hoja.py --hojas data/dataset_v2/train --coco 900
    python vision/train/filtro_hoja.py --hojas data/dataset_v2/train \\
        --objetos data/dataset_v2/train/sin_hoja data/raw/propias/sin_hoja --coco 900

Escribe filtro_hoja en vision/models/sigatoka_cls_v2.json (o el JSON de --modelo). La página
web, la estación y el dron lo usan al cargar el modelo; sin él, todo funciona como antes.
"""
import argparse
import json
import random
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import Clasificador, leer_imagen  # noqa: E402
from vision.rasgos import color_hoja, con_rasgos  # noqa: E402

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
COCO_LISTA = "http://images.cocodataset.org/annotations/image_info_test2017.zip"
COCO_FOTO = "http://images.cocodataset.org/test2017/{}"


def fotos(carpetas: list[Path], saltar: set[str]) -> list[Path]:
    lista = []
    for c in carpetas:
        for f in sorted(c.rglob("*")):
            if f.suffix.lower() in EXT and not (set(f.relative_to(c).parts[:-1]) & saltar):
                lista.append(f)
    return lista


def bajar_coco(n: int, destino: Path) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    ya = sorted(destino.glob("*.jpg"))
    if len(ya) >= n:
        return ya[:n]
    print(f"Bajando {n - len(ya)} fotos de COCO a {destino} ...", flush=True)
    with urllib.request.urlopen(COCO_LISTA, timeout=120) as r:
        z = zipfile.ZipFile(BytesIO(r.read()))
    info = json.loads(z.read("annotations/image_info_test2017.json"))
    nombres = [i["file_name"] for i in info["images"]]
    random.Random(7).shuffle(nombres)
    faltan = [x for x in nombres if not (destino / x).exists()][:n - len(ya)]

    def una(nombre):
        try:
            with urllib.request.urlopen(COCO_FOTO.format(nombre), timeout=60) as r:
                (destino / nombre).write_bytes(r.read())
        except OSError as e:
            print(f"  no se pudo bajar {nombre}: {e}")

    with ThreadPoolExecutor(16) as ex:
        list(ex.map(una, faltan))
    return sorted(destino.glob("*.jpg"))[:n]


class Rasgos:
    def __init__(self, ruta_onnx: Path):
        self.c = Clasificador(ruta_onnx)
        datos, self.nombre, self.W, self.b = con_rasgos(ruta_onnx.read_bytes())
        prov = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
        self.sesion = ort.InferenceSession(datos, providers=prov)
        self.entrada = self.sesion.get_inputs()[0].name
        self.cfg = self.c.cfg_parches
        self.ignorar = [self.c.clases.index(k) for k in (self.cfg.get("ignorar") or []) if k in self.c.clases]

    def de(self, img: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(rasgos N x D, ¿el modelo lo lee como hoja de plátano? N, color de hoja N) de los cuadros."""
        cuadros = P.cuadros(img, self.cfg, P.mascara_hoja(img))
        x = np.stack([self.c._tensor(P.recortar(img, q), cv2.INTER_AREA) for q in cuadros])
        partes = [self.sesion.run(None, {self.entrada: x[i:i + 16]}) for i in range(0, len(x), 16)]
        p = np.concatenate([s[0] for s in partes])
        f = np.concatenate([s[1] for s in partes]).astype(np.float32)
        return f, ~np.isin(p.argmax(1), self.ignorar), np.array([color_hoja(t) for t in x])

    def completa(self, img: np.ndarray) -> tuple[np.ndarray, bool]:
        """(rasgos D, ¿el modelo la lee como hoja?) de la foto completa reducida (video en vivo)."""
        p, f = self.sesion.run(None, {self.entrada: self.c._tensor(img, cv2.INTER_LINEAR)[None]})
        return f[0].astype(np.float32), int(p[0].argmax()) not in self.ignorar


def acercamiento(img: np.ndarray, rnd: random.Random) -> np.ndarray:
    h, w = img.shape[:2]
    k = rnd.uniform(0.3, 0.6)
    ch, cw = max(8, int(h * k)), max(8, int(w * k))
    y, x = rnd.randint(0, h - ch), rnd.randint(0, w - cw)
    z = cv2.resize(img[y:y + ch, x:x + cw], (2016, 1512), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(z, (0, 0), rnd.uniform(0.5, 1.5))


def entrenar(X: np.ndarray, y: np.ndarray, lam: float, vueltas: int = 400, paso: float = 0.05):
    """Regresión logística (Adam, L2, clases equilibradas). Devuelve (w, b) sobre rasgos crudos."""
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = ((X - mu) / sd).astype(np.float32)
    peso = np.where(y == 1, (y == 0).sum() / max(1, (y == 1).sum()), 1.0).astype(np.float32)
    peso /= peso.mean()
    w = np.zeros(Z.shape[1], np.float32)
    b = 0.0
    m = np.zeros_like(w)
    v = np.zeros_like(w)
    mb = vb = 0.0
    for t in range(1, vueltas + 1):
        s = 1 / (1 + np.exp(-np.clip(Z @ w + b, -30, 30)))
        g = peso * (s - y)
        gw = Z.T @ g / len(y) + lam * w
        gb = float(g.mean())
        m = 0.9 * m + 0.1 * gw
        v = 0.999 * v + 0.001 * gw ** 2
        mb = 0.9 * mb + 0.1 * gb
        vb = 0.999 * vb + 0.001 * gb ** 2
        w -= paso * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
        b -= paso * (mb / (1 - 0.9 ** t)) / (np.sqrt(vb / (1 - 0.999 ** t)) + 1e-8)
    return w / sd, float(b - (w * mu / sd).sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", type=Path, default=RAIZ / "vision/models/sigatoka_cls_v2.onnx")
    ap.add_argument("--hojas", type=Path, nargs="+", required=True, help="carpetas con fotos de hoja de plátano")
    ap.add_argument("--objetos", type=Path, nargs="*", default=[], help="carpetas con fotos que no son hoja de plátano")
    ap.add_argument("--coco", type=int, default=0, help="además, N fotos de COCO como objetos (se bajan una vez)")
    ap.add_argument("--carpeta-coco", type=Path, default=RAIZ / "data/raw/objetos_coco")
    ap.add_argument("--max-fotos", type=int, default=1500, help="máximo de fotos de hoja (al azar)")
    ap.add_argument("--max-objetos", type=int, default=2000, help="máximo de fotos de objetos, contando las de COCO")
    ap.add_argument("--umbral", type=float, default=-3.0)
    ap.add_argument("--umbral-verde", type=float, default=None,
                    help="otro umbral para cuadros con color de hoja (por omisión, el mismo)")
    ap.add_argument("--verde-min", type=float, default=0.2, help="fracción del cuadro con color de hoja")
    ap.add_argument("--modo", choices=["foto", "cuadro"], default="foto")
    ap.add_argument("--umbral-imagen", type=float, default=-3.0, help="sonda de la foto completa (video en vivo)")
    ap.add_argument("--lam", type=float, default=1e-2, help="regularización L2")
    ap.add_argument("--apartar", type=float, default=0.2, help="fracción de fotos para el reporte")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.umbral_verde is None:
        args.umbral_verde = args.umbral

    rnd = random.Random(args.seed)
    R = Rasgos(args.modelo)
    saltar = set(R.cfg.get("ignorar") or [])
    hojas = fotos(args.hojas, saltar)
    rnd.shuffle(hojas)
    hojas = hojas[:args.max_fotos]
    coco = bajar_coco(args.coco, args.carpeta_coco) if args.coco else []
    objetos = fotos(args.objetos, set())
    rnd.shuffle(objetos)
    objetos = objetos[:max(0, args.max_objetos - len(coco))] + coco
    rnd.shuffle(objetos)
    if not hojas or not objetos:
        sys.exit("Hacen falta fotos de hoja (--hojas) y de objetos (--objetos o --coco).")
    print(f"{len(hojas)} fotos de hoja, {len(objetos)} de objetos (más un acercamiento de cada una)", flush=True)

    def leer(lista, con_acercamiento):
        out = []
        for k, f in enumerate(lista, 1):
            img = leer_imagen(f)
            if img is None or img.ndim != 3:
                continue
            for im in ([img, acercamiento(img, rnd)] if con_acercamiento else [img]):
                out.append((R.de(im), R.completa(im)))
            if k % 200 == 0:
                print(f"  {k}/{len(lista)}", flush=True)
        return out

    H = leer(hojas, False)
    O = leer(objetos, True)
    corte_h, corte_o = int(len(H) * (1 - args.apartar)), int(len(O) * (1 - args.apartar)) // 2 * 2
    Htr, Hte, Otr, Ote = H[:corte_h], H[corte_h:], O[:corte_o], O[corte_o:]

    def XY(hs, os_):
        Xp = np.concatenate([F[es] for (F, es, _), _ in hs])
        Xn = np.concatenate([F for (F, _, _), _ in os_])
        return np.concatenate([Xp, Xn]), np.concatenate([np.ones(len(Xp), np.float32), np.zeros(len(Xn), np.float32)])

    def XY_imagen(hs, os_):
        Xp = np.stack([f for _, (f, es) in hs if es])
        Xn = np.stack([f for _, (f, _) in os_])
        return np.concatenate([Xp, Xn]), np.concatenate([np.ones(len(Xp), np.float32), np.zeros(len(Xn), np.float32)])

    X, y = XY(Htr, Otr)
    print(f"Entrenando con {int(y.sum())} cuadros de hoja y {int((1 - y).sum())} de objetos ...", flush=True)
    w, b = entrenar(X, y, args.lam)

    # Reporte con lo apartado: una foto "deja de ser hoja" si ninguno de sus cuadros de hoja pasa.
    def pasa(F, es, col, u, uv):
        return es & (F @ w + b >= np.where(col >= args.verde_min, uv, u))

    print("\numbral verde / sin verde | fotos de hoja apartadas que se quedan sin hoja"
          " | objetos apartados que aún se leen como hoja")
    antes = sum(es.any() for (_, es, _), _ in Ote)
    for uv in [-5, -4, -3, -2]:
        for u in sorted({uv, args.umbral} if args.umbral != args.umbral_verde else {uv}):
            pierde = sum(es.any() and not pasa(F, es, col, u, uv).any() for (F, es, col), _ in Hte)
            quedan = sum(pasa(F, es, col, u, uv).any() for (F, es, col), _ in Ote)
            marca = "  <- elegido" if (uv, u) == (args.umbral_verde, args.umbral) else ""
            print(f"{uv:5.1f} / {u:5.1f} | {pierde:4d} de {len(Hte):4d} | {quedan:4d} de {len(Ote)} (sin filtro: {antes}){marca}")

    wi, bi = entrenar(*XY_imagen(Htr, Otr), args.lam)
    print("\nVideo en vivo (foto completa) | fotos de hoja apartadas que pasan a sin hoja | objetos apartados que aún se leen como hoja")
    antes = sum(es for _, (_, es) in Ote)
    for t in [-5, -4, -3, -2, -1]:
        pierde = sum(es and f @ wi + bi < t for _, (f, es) in Hte)
        quedan = sum(es and f @ wi + bi >= t for _, (f, es) in Ote)
        marca = "  <- elegido" if t == args.umbral_imagen else ""
        print(f"{t:5.1f} | {pierde:4d} de {len(Hte):4d} | {quedan:4d} de {len(Ote)} (sin filtro: {antes}){marca}")

    # Final: con todas las fotos.
    wi, bi = entrenar(*XY_imagen(H, O), args.lam)
    X, y = XY(H, O)
    w, b = entrenar(X, y, args.lam)
    ruta_json = args.modelo.with_suffix(".json")
    meta = json.loads(ruta_json.read_text(encoding="utf-8"))
    meta["filtro_hoja"] = {
        "descripcion": "Sonda lineal sobre los rasgos de cada cuadro: hoja de plátano contra objetos cotidianos. "
                       "modo foto: si ningún cuadro de hoja tiene w · rasgos + b >= umbral, la foto cuenta como sin hoja; "
                       "si alguno pasa, el veredicto es el del modelo con todos sus cuadros. Ver vision/train/filtro_hoja.py.",
        "rasgos": R.nombre,
        "modo": args.modo,
        "umbral": args.umbral,
        "umbral_verde": args.umbral_verde,
        "verde_min": args.verde_min,
        "b": round(b, 5),
        "w": [float(f"{x:.4g}") for x in w],
        "entrenado": {"fecha": date.today().isoformat(), "fotos_hoja": len(hojas), "fotos_objetos": len(objetos),
                      "cuadros_hoja": int(y.sum()), "cuadros_objetos": int((1 - y).sum())},
        "imagen": {
            "descripcion": "Sonda para la foto completa reducida (video en vivo del dron). "
                           "Si w · rasgos + b < umbral, la imagen cuenta como sin hoja.",
            "umbral": args.umbral_imagen,
            "b": round(bi, 5),
            "w": [float(f"{x:.4g}") for x in wi],
        },
    }
    ruta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nfiltro_hoja guardado en {ruta_json}")


if __name__ == "__main__":
    main()
