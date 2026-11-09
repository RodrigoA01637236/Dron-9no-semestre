"""Junta los datasets públicos en data/dataset_v2 sin duplicados ni fugas entre train y test.

Qué hace:
1. Lee las fuentes de vision/train/fuentes_v2.json (las que no estén descargadas se saltan).
2. Pone la clase según el nombre de la carpeta ('mapa' o 'palabras' del JSON). Una fuente
   con 'clase_fija' (p. ej. fotos de otras plantas o de escenas sin plátano) va completa a
   esa clase ("sin_hoja"); 'max_imagenes' toma una muestra fija de las fuentes grandes.
3. Quita duplicados exactos (md5) y agrupa los casi duplicados (dHash de 256 bits con
   giros y espejos): un grupo entero va al mismo split, así una foto y su copia girada no
   quedan una en train y otra en test. Una misma foto (mismo md5) con dos etiquetas se
   deja fuera; fotos parecidas con etiquetas distintas se quedan, cada una con la suya.
   Las dos cosas se anotan en data/manifests/v2_conflictos.csv para que alguien las revise.
4. Respeta el reparto del manifiesto v1: lo que fue test en v1 sigue en test, para que la
   comparación v1 contra v2 sea justa (v1 nunca vio esas fotos).
5. Reparte el resto 70/15/15 por clase. Las fuentes con uso 'externo' van completas a
   test_<nombre>/ y se les quitan las fotos repetidas de train.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/preparar_datos.py
    python vision/train/preparar_datos.py --fuentes vision/train/fuentes_v2.json --out data/dataset_v2

Sale: data/dataset_v2/{train,val,test,test_<externo>}/<clase>/ (enlaces o copias),
data/manifests/v2_publico.csv (va a git) y data/dataset_v2/resumen.json.
Ver vision/GUIA-PARCHES.md, paso 2.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import cv2
import numpy as np

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
REPARTO = {"train": 0.70, "val": 0.15, "test": 0.15}


def normal(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return " ".join(t.replace("_", " ").replace("-", " ").split())


def leer_gris(ruta: Path) -> np.ndarray | None:
    try:
        datos = np.fromfile(str(ruta), dtype=np.uint8)
    except OSError:
        return None
    if datos.size == 0:
        return None
    return cv2.imdecode(datos, cv2.IMREAD_REDUCED_GRAYSCALE_4)


LADO_HASH = 16  # 16x16 = 256 bits; con 8x8 las hojas de fondo liso se confunden entre sí


def dhashes(gris: np.ndarray) -> np.ndarray:
    """dHash de la imagen en sus 8 giros/espejos (para casar copias aumentadas): (8, 4) uint64."""
    t = cv2.resize(gris, (LADO_HASH + 1, LADO_HASH + 1), interpolation=cv2.INTER_AREA).astype(np.int16)
    salida = []
    for k in range(4):
        r = np.rot90(t, k)
        for m in (r, r[:, ::-1]):
            bits = (m[:LADO_HASH, 1:] > m[:LADO_HASH, :-1]).ravel()
            salida.append(np.packbits(bits).view(">u8").astype(np.uint64))
    return np.stack(salida)


_POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def popcount(x: np.ndarray) -> np.ndarray:
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    return _POP[x.view(np.uint8)].reshape(*x.shape, 8).sum(-1)


class Grupos:
    def __init__(self, n):
        self.p = list(range(n))

    def raiz(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def unir(self, a, b):
        self.p[self.raiz(a)] = self.raiz(b)


# ------------------------------------------------------------------ recolección

def clase_de(rel: Path, fuente: dict, cfg: dict) -> str | None:
    mapa = {normal(k): v for k, v in (fuente.get("mapa") or {}).items()}
    for carpeta in reversed(rel.parts[:-1]):  # de la carpeta de la foto hacia arriba
        n = normal(carpeta)
        if n in mapa:
            return mapa[n]
        for clase, palabras in cfg["palabras"].items():
            if any(p in n for p in palabras):
                return clase
    return None


def recolectar_carpetas(fuente: dict, cfg: dict, raiz: Path, avisos: Counter) -> list[dict]:
    excluir = [normal(e) for e in cfg.get("excluir", [])] + [normal(e) for e in fuente.get("excluir", [])]
    fija = fuente.get("clase_fija")
    items = []
    for ruta in sorted(raiz.rglob("*")):
        if ruta.suffix.lower() not in IMG_EXTS or ruta.name.startswith(".") or not ruta.is_file():
            continue  # ._foto.jpg y .DS_Store son basura de macOS dentro de los zip
        rel = ruta.relative_to(raiz)
        if any(e in normal(p) for p in rel.parts[:-1] for e in excluir):
            avisos[f"{fuente['nombre']}: excluida ({rel.parts[0]})"] += 1
            continue
        clase = fija or clase_de(rel, fuente, cfg)
        if clase is None:
            avisos[f"{fuente['nombre']}: carpeta sin clase '{rel.parent}' (agrégala a 'mapa')"] += 1
            continue
        items.append({"ruta": ruta, "rel": rel, "clase": clase, "fuente": fuente["nombre"],
                      "uso": fuente["uso"], "cajas": None})
    return items


def recolectar_yolo(fuente: dict, raiz: Path, avisos: Counter) -> list[dict]:
    """Formato YOLO: images/x.jpg + labels/x.txt (clase cx cy w h normalizados)."""
    mapa = {int(k): v for k, v in fuente.get("clases_yolo", {"0": "sigatoka"}).items()}
    items = []
    for ruta in sorted(raiz.rglob("*")):
        if ruta.suffix.lower() not in IMG_EXTS or ruta.name.startswith(".") or not ruta.is_file():
            continue
        if "__macosx" in str(ruta).lower():
            continue
        partes = list(ruta.parts)
        if "images" in partes:
            partes[len(partes) - 1 - partes[::-1].index("images")] = "labels"
        etiqueta = Path(*partes).with_suffix(".txt")
        if not etiqueta.exists():
            etiqueta = ruta.with_suffix(".txt")
        cajas, clases = [], Counter()
        if etiqueta.exists():
            for linea in etiqueta.read_text(encoding="utf-8", errors="ignore").splitlines():
                v = linea.split()
                if len(v) >= 5 and int(float(v[0])) in mapa:
                    clases[mapa[int(float(v[0]))]] += 1
                    cajas.append([float(x) for x in v[1:5]])
        if not clases:
            avisos[f"{fuente['nombre']}: imagen sin cajas de una clase conocida (se omite)"] += 1
            continue
        items.append({"ruta": ruta, "rel": ruta.relative_to(raiz), "clase": clases.most_common(1)[0][0],
                      "fuente": fuente["nombre"], "uso": fuente["uso"], "cajas": cajas})
    return items


# ------------------------------------------------------------------ principal

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuentes", default="vision/train/fuentes_v2.json")
    ap.add_argument("--out", default="data/dataset_v2")
    ap.add_argument("--manifest", default="data/manifests/v2_publico.csv")
    ap.add_argument("--respetar", default="data/manifests/v1_public_baseline.csv",
                    help="manifiesto v1 cuyo reparto se conserva (si existe)")
    ap.add_argument("--distancia", type=int, default=12,
                    help="bits (de 256) de diferencia para casi duplicado. Copias giradas o recomprimidas: 0-2; "
                         "fotos distintas: 50+; tomas seguidas del mismo objeto: 15-25")
    ap.add_argument("--copiar", action="store_true", help="copiar en vez de enlazar (más espacio)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cfg = json.loads(Path(args.fuentes).read_text(encoding="utf-8"))
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} ya existe: bórralo (o usa otro --out) para regenerar desde cero.")

    # 1. Recolectar
    avisos: Counter = Counter()
    items: list[dict] = []
    for f in cfg["fuentes"]:
        raiz = Path(f["carpeta"])
        if not raiz.is_dir():
            print(f"  (sin descargar) {f['nombre']:14s} {raiz}")
            continue
        nuevos = recolectar_yolo(f, raiz, avisos) if f.get("formato") == "yolo" else \
            recolectar_carpetas(f, cfg, raiz, avisos)
        tope = int(f.get("max_imagenes") or 0)
        if tope and len(nuevos) > tope:
            nuevos = random.Random(args.seed).sample(nuevos, tope)
        conteo = Counter(i["clase"] for i in nuevos)
        print(f"  {f['nombre']:14s} {len(nuevos):6d} imágenes  {dict(sorted(conteo.items()))}  [{f['uso']}]")
        items += nuevos
    for a, n in sorted(avisos.items()):
        print(f"  AVISO {a}: {n}")
    if not items:
        sys.exit("No encontré imágenes. Revisa las carpetas de vision/train/fuentes_v2.json.")

    # 2. Huellas (md5 y dHash)
    print(f"\nCalculando huellas de {len(items)} imágenes...")
    hashes = np.zeros((len(items), 8, LADO_HASH * LADO_HASH // 64), dtype=np.uint64)
    validos = []
    for k, it in enumerate(items):
        it["md5"] = hashlib.md5(it["ruta"].read_bytes()).hexdigest()
        g = leer_gris(it["ruta"])
        if g is None or min(g.shape) < 9:
            avisos["no se pudo leer"] += 1
            continue
        hashes[k] = dhashes(g)
        validos.append(k)
        if (k + 1) % 2000 == 0:
            print(f"  {k + 1}/{len(items)}")
    items = [items[k] for k in validos]
    hashes = hashes[validos]
    n = len(items)

    # 3. Agrupar duplicados exactos y casi duplicados
    grupos = Grupos(n)
    por_md5 = defaultdict(list)
    for k, it in enumerate(items):
        por_md5[it["md5"]].append(k)
    for ks in por_md5.values():
        for k in ks[1:]:
            grupos.unir(ks[0], k)
    base = hashes[:, 0].copy()
    for k in range(n - 1):
        d = popcount(hashes[k + 1:] ^ base[k]).sum(axis=2).min(axis=1)
        for j in np.nonzero(d <= args.distancia)[0]:
            grupos.unir(k, k + 1 + int(j))
    miembros = defaultdict(list)
    for k in range(n):
        miembros[grupos.raiz(k)].append(k)
    grandes = sorted((len(ks) for ks in miembros.values() if len(ks) > 1), reverse=True)
    print(f"  {len(miembros)} grupos; {len(grandes)} con repetidas; los más grandes: {grandes[:5]}")
    if grandes and grandes[0] > 50:
        print("  AVISO: un grupo de más de 50 fotos suele ser fotos casi lisas (oscuras, borrosas)."
              " Revisa v2_publico.csv por 'grupo' o baja --distancia.")

    # 4. Reparto
    forzado = {}
    if Path(args.respetar).exists():
        with open(args.respetar, encoding="utf-8") as fh:
            for fila in csv.DictReader(fh):
                nombre = Path(fila["path"]).name.split("__", 1)[-1]
                forzado[(normal(fila["origen"]), nombre)] = fila["split"]
        print(f"Reparto de {args.respetar}: {len(forzado)} imágenes conservan su split")

    rng = random.Random(args.seed)
    conflictos, filas = [], []
    pendientes = defaultdict(list)          # clase -> grupos sin split forzado
    asignado = Counter()                     # (clase, split) -> imágenes
    destino_grupo = {}
    externos_md5 = set()

    mixtos = []
    for raiz_g, ks in list(miembros.items()):
        # La misma foto con dos etiquetas: no se sabe cuál es la buena, se quita.
        etiquetas_md5 = defaultdict(set)
        for k in ks:
            etiquetas_md5[items[k]["md5"]].add(items[k]["clase"])
        malos = [k for k in ks if len(etiquetas_md5[items[k]["md5"]]) > 1]
        if malos:
            conflictos.append(malos)
            ks = [k for k in ks if k not in malos]
            miembros[raiz_g] = ks
            if not ks:
                continue
        votos_clase = Counter(items[k]["clase"] for k in ks)
        if len(votos_clase) > 1:
            mixtos.append(ks)  # fotos parecidas con etiqueta distinta: se quedan, mismo split
        clase = votos_clase.most_common(1)[0][0]
        usos = {items[k]["uso"] for k in ks}
        if usos == {"externo"}:
            destino_grupo[raiz_g] = "externo"
            continue
        if "solo_entrenar" in usos:
            destino_grupo[raiz_g] = "train"
            asignado[(clase, "train")] += len(ks)
            continue
        splits = set()
        for k in ks:
            it = items[k]
            if it["fuente"] == "v1_publico" and it["uso"] == "entrenar":
                s = forzado.get((normal(it["rel"].parts[0]), it["rel"].name))
                if s:
                    splits.add(s)
        if splits:
            s = "train" if "train" in splits else ("val" if "val" in splits else "test")
            destino_grupo[raiz_g] = s
            asignado[(clase, s)] += len(ks)
        else:
            pendientes[clase].append(raiz_g)

    for clase, gs in pendientes.items():
        rng.shuffle(gs)
        total = sum(len(miembros[g]) for g in gs) + sum(asignado[(clase, s)] for s in REPARTO)
        for g in gs:
            # al split con más faltante respecto a su meta
            s = max(REPARTO, key=lambda s: REPARTO[s] * total - asignado[(clase, s)])
            destino_grupo[g] = s
            asignado[(clase, s)] += len(miembros[g])

    # 5. Materializar: todo el grupo al mismo split; las copias exactas (mismo md5) una sola vez.
    # Si un grupo mezcla una fuente externa con una de entrenar, la externa pierde esas fotos:
    # así la prueba externa no trae fotos que el modelo ya vio.
    def poner(origen: Path, destino: Path):
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not args.copiar:
            try:
                os.link(origen, destino)
                return
            except OSError:
                pass
        shutil.copy2(origen, destino)

    cajas_ext = defaultdict(dict)
    usados = set()
    for raiz_g, s in destino_grupo.items():
        ks = miembros[raiz_g]
        mixto = s != "externo" and any(items[k]["uso"] == "externo" for k in ks)
        vistos_md5 = set()
        for k in ks:
            it = items[k]
            carpeta = f"test_{it['fuente']}" if s == "externo" else s
            fila = {"path": "", "origen": it["fuente"],
                    "archivo_original": str(it["rel"]).replace("\\", "/"),
                    "etiqueta": it["clase"], "split": carpeta, "grupo": raiz_g,
                    "duplicado": 0, "md5": it["md5"], "fecha": date.today().isoformat()}
            if it["md5"] in vistos_md5 or (mixto and it["uso"] == "externo"):
                fila["duplicado"] = 1
                filas.append(fila)
                continue
            vistos_md5.add(it["md5"])
            nombre = f"{it['fuente']}__{'_'.join(it['rel'].with_suffix('').parts)}{it['ruta'].suffix.lower()}"
            nombre = nombre.replace(" ", "_")
            while nombre in usados:
                nombre = "x" + nombre
            usados.add(nombre)
            poner(it["ruta"], out / carpeta / it["clase"] / nombre)
            if it["cajas"] is not None:
                cajas_ext[carpeta][nombre] = it["cajas"]
            fila["path"] = f"{carpeta}/{it['clase']}/{nombre}"
            filas.append(fila)

    for carpeta, cajas in cajas_ext.items():
        (out / carpeta / "cajas_yolo.json").write_text(json.dumps(cajas), encoding="utf-8")

    # 6. Manifiesto, conflictos y resumen
    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(sorted(filas, key=lambda f: (f["split"], f["etiqueta"], f["path"])))
    if conflictos or mixtos:
        ruta_c = manifest.with_name("v2_conflictos.csv")
        with open(ruta_c, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["grupo", "accion", "origen", "archivo_original", "etiqueta"])
            for lista, accion in ((conflictos, "quitada: misma foto con dos etiquetas"),
                                  (mixtos, "se queda: foto parecida con otra etiqueta")):
                for ks in lista:
                    for k in ks:
                        w.writerow([ks[0], accion, items[k]["fuente"], str(items[k]["rel"]), items[k]["clase"]])
        print(f"\n{sum(map(len, conflictos))} fotos idénticas con dos etiquetas quedaron fuera; "
              f"{len(mixtos)} grupos de fotos parecidas tienen etiquetas distintas (se quedan). Ver {ruta_c}")

    conteo = Counter((f["split"], f["etiqueta"]) for f in filas if f["path"])
    splits = sorted({s for s, _ in conteo})
    resumen = {"fecha": date.today().isoformat(), "fuentes": args.fuentes,
               "imagenes_leidas": n, "duplicados_quitados": sum(f["duplicado"] for f in filas),
               "fotos_en_conflicto": sum(map(len, conflictos)), "grupos_mixtos": len(mixtos),
               "conteo": {s: {c: conteo[(s, c)] for c in cfg["clases"]} for s in splits}}
    (out / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nCopias exactas quitadas: {resumen['duplicados_quitados']}")
    print(f"{'split':24s}" + "".join(f"{c:>16s}" for c in cfg["clases"]))
    for s in splits:
        print(f"{s:24s}" + "".join(f"{conteo[(s, c)]:16d}" for c in cfg["clases"]))
    print(f"\nManifiesto: {manifest}\nDataset: {out}")
    print("Siguiente paso: python vision/train/hacer_parches.py --maestro vision/models/sigatoka_cls_v1.onnx")


if __name__ == "__main__":
    main()
