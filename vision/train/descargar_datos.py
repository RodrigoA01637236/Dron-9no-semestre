"""Descarga y descomprime las fuentes públicas de vision/train/fuentes_v2.json.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/descargar_datos.py --lista          # qué hay, cuánto pesa y si ya está
    python vision/train/descargar_datos.py                  # todo lo recomendado (sin las de más de 30 GB)
    python vision/train/descargar_datos.py --con-grandes    # también Tanzania-Zenodo (34 GB)
    python vision/train/descargar_datos.py --solo nmaist,peru

- Las descargas grandes se reanudan si se cortan: vuelve a correr el mismo comando.
- Al terminar cada fuente se borran los comprimidos (--guardar-comprimidos para dejarlos).
- Los .rar se abren con 7-Zip (https://7-zip.org) o con el tar de Windows 10/11.
- Las fuentes "manual" (DeepWeeds está en Google Drive) solo se explican: hay que bajarlas
  con el navegador.
- Una fuente terminada deja <carpeta>/.descarga_completa y no se vuelve a bajar.
Ver vision/GUIA-NOCHE.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AGENTE = {"User-Agent": "dron-sigatoka-descargas/1.0"}
COMPRIMIDOS = (".zip", ".rar", ".7z", ".tar", ".gz", ".tgz")
MARCA = ".descarga_completa"


def pedir_json(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def bajar(url: str, destino: Path, mostrar: bool = True) -> Path:
    """Descarga con reanudación (Range) y 5 intentos."""
    if destino.exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    parte = destino.with_name(destino.name + ".parte")
    for intento in range(5):
        hecho = parte.stat().st_size if parte.exists() else 0
        cab = dict(AGENTE, **({"Range": f"bytes={hecho}-"} if hecho else {}))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=120) as r:
                if hecho and r.status != 206:
                    hecho = 0  # el servidor no reanuda: desde cero
                total = hecho + int(r.headers.get("Content-Length") or 0)
                ultimo = time.time()
                with open(parte, "ab" if hecho else "wb") as f:
                    while bloque := r.read(1 << 20):
                        f.write(bloque)
                        hecho += len(bloque)
                        if mostrar and time.time() - ultimo > 5:
                            ultimo = time.time()
                            pct = f"{100 * hecho / total:.0f} %" if total else ""
                            print(f"    {destino.name}: {hecho / 2**30:.2f} GB {pct}", flush=True)
            parte.rename(destino)
            return destino
        except (OSError, urllib.error.URLError) as e:
            espera = 2 ** (intento + 1)
            print(f"    {destino.name}: se cortó ({e}); reintento en {espera} s", flush=True)
            time.sleep(espera)
    raise RuntimeError(f"No se pudo bajar {url}")


def descomprimir(archivo: Path, destino: Path) -> None:
    print(f"    descomprimiendo {archivo.name}...", flush=True)
    if archivo.suffix.lower() == ".zip":
        with zipfile.ZipFile(archivo) as z:
            for m in z.infolist():
                nombre = Path(m.filename)
                if "__MACOSX" in nombre.parts or nombre.name.startswith("._"):
                    continue
                z.extract(m, destino)
        return
    siete = shutil.which("7z") or next((p for p in (r"C:\Program Files\7-Zip\7z.exe",
                                                    r"C:\Program Files (x86)\7-Zip\7z.exe") if Path(p).exists()), None)
    intentos = ([[siete, "x", "-y", f"-o{destino}", str(archivo)]] if siete else []) + \
        [["tar", "-xf", str(archivo), "-C", str(destino)]]
    for cmd in intentos:
        try:
            if subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE).returncode == 0:
                return
        except FileNotFoundError:
            continue
    raise RuntimeError(f"No pude abrir {archivo.name}. Instala 7-Zip (https://7-zip.org) y vuelve a correr.")


# ------------------------------------------------------------------ por tipo de fuente

def mendeley(desc: dict, carpeta: Path, excluir: list[str]) -> list[Path]:
    ds = pedir_json(f"https://data.mendeley.com/public-api/datasets/{desc['id']}")
    carpetas = pedir_json(f"https://data.mendeley.com/public-api/datasets/{desc['id']}/folders/{ds['version']}")
    por_id = {c["id"]: c for c in carpetas}

    def ruta_carpeta(fid):
        partes = []
        while fid and fid in por_id:
            partes.append(por_id[fid]["name"])
            fid = por_id[fid].get("parent_id")
        return Path(*reversed(partes)) if partes else Path()

    tareas = []
    for f in ds["files"]:
        rel = ruta_carpeta(f.get("folder_id")) / f["filename"]
        if any(e in str(rel).lower() for e in excluir):
            continue
        tareas.append((f["content_details"]["download_url"], carpeta / rel, f.get("size", 0)))
    total = sum(t[2] for t in tareas)
    print(f"    Mendeley {desc['id']} v{ds['version']}: {len(tareas)} archivos, {total / 2**30:.2f} GB", flush=True)
    grandes = [t for t in tareas if t[2] > 50 * 2**20]
    chicos = [t for t in tareas if t[2] <= 50 * 2**20]
    hechos = 0
    with ThreadPoolExecutor(8) as pool:
        for _ in pool.map(lambda t: bajar(t[0], t[1], mostrar=False), chicos):
            hechos += 1
            if hechos % 500 == 0:
                print(f"    {hechos}/{len(chicos)} archivos", flush=True)
    for url, destino, _ in grandes:
        bajar(url, destino)
    return [d for _, d, _ in tareas if d.suffix.lower() in COMPRIMIDOS]


def zenodo(desc: dict, carpeta: Path, descargas: Path) -> list[Path]:
    rec = pedir_json(f"https://zenodo.org/api/records/{desc['id']}")
    querer = set(desc.get("archivos") or [])
    salida = []
    for f in rec["files"]:
        if querer and f["key"] not in querer:
            continue
        print(f"    {f['key']} ({f['size'] / 2**30:.1f} GB)", flush=True)
        salida.append(bajar(f["links"]["self"], descargas / f["key"]))
    return salida


def dataverse(desc: dict, descargas: Path) -> list[Path]:
    salida = []
    for fid, nombre in desc["archivos"].items():
        print(f"    {nombre}", flush=True)
        salida.append(bajar(f"https://dataverse.harvard.edu/api/access/datafile/{fid}", descargas / nombre))
    return salida


def urls(desc: dict, descargas: Path) -> list[Path]:
    salida = []
    for u in desc["urls"]:
        nombre = u.rstrip("/").split("/")[-1]
        print(f"    {nombre}", flush=True)
        salida.append(bajar(u, descargas / nombre))
    return salida


def filtrar_coco(carpeta: Path) -> None:
    """Quita las fotos de COCO que tienen plátano o plantas en maceta (no son 'sin hoja')."""
    anot = next(carpeta.rglob("instances_val2017.json"), None)
    if anot is None:
        print("    AVISO: no encontré instances_val2017.json; no se filtró COCO.")
        return
    d = json.loads(anot.read_text(encoding="utf-8"))
    malas = {c["id"] for c in d["categories"] if c["name"] in ("banana", "potted plant")}
    quitar = {a["image_id"] for a in d["annotations"] if a["category_id"] in malas}
    nombres = {i["id"]: i["file_name"] for i in d["images"]}
    n = 0
    for iid in quitar:
        for p in carpeta.rglob(nombres[iid]):
            p.unlink()
            n += 1
    shutil.rmtree(anot.parent, ignore_errors=True)
    print(f"    COCO: quité {n} fotos con plátano o plantas en maceta", flush=True)


# ------------------------------------------------------------------ principal

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuentes", default="vision/train/fuentes_v2.json")
    ap.add_argument("--lista", action="store_true", help="solo mostrar las fuentes")
    ap.add_argument("--solo", default="", help="nombres separados por coma")
    ap.add_argument("--con-grandes", action="store_true", help="incluir las fuentes marcadas 'grande' (34 GB)")
    ap.add_argument("--guardar-comprimidos", action="store_true")
    args = ap.parse_args()

    os.chdir(RAIZ)
    cfg = json.loads(Path(args.fuentes).read_text(encoding="utf-8"))
    solo = {s.strip() for s in args.solo.split(",") if s.strip()}
    fuentes = [f for f in cfg["fuentes"] if f.get("descarga") and (not solo or f["nombre"] in solo)]

    if args.lista:
        print(f"{'fuente':20s} {'GB':>6s}  {'tipo':10s} {'uso':14s} estado")
        for f in fuentes:
            listo = (Path(f["carpeta"]) / MARCA).exists()
            print(f"{f['nombre']:20s} {f.get('tamano_gb', 0):6.2f}  {f['descarga']['tipo']:10s} "
                  f"{f.get('clase_fija') or f['uso']:14s} {'lista' if listo else ('GRANDE (--con-grandes)' if f.get('grande') else 'pendiente')}")
        return

    total = sum(f.get("tamano_gb", 0) for f in fuentes
                if not (Path(f["carpeta"]) / MARCA).exists() and (args.con_grandes or not f.get("grande") or f["nombre"] in solo))
    libre = shutil.disk_usage(RAIZ).free / 2**30
    print(f"Por bajar: ~{total:.0f} GB (y algo parecido al descomprimir). Libre: {libre:.0f} GB.")
    if libre < 2.2 * total:
        print("AVISO: puede faltar espacio. Usa --solo para bajar por partes.")

    manuales, fallas = [], []
    for f in fuentes:
        carpeta = Path(f["carpeta"])
        desc = f["descarga"]
        if (carpeta / MARCA).exists():
            print(f"= {f['nombre']}: ya está")
            continue
        if f.get("grande") and not args.con_grandes and f["nombre"] not in solo:
            print(f"- {f['nombre']}: se salta ({f.get('tamano_gb')} GB; usa --con-grandes)")
            continue
        if desc["tipo"] == "manual":
            manuales.append(f)
            continue
        print(f"\n> {f['nombre']} ({f.get('tamano_gb', '?')} GB) -> {carpeta}", flush=True)
        descargas = Path("data/raw/descargas") / f["nombre"]
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            excluir = [e.lower() for e in cfg.get("excluir", []) + desc.get("excluir", []) if e != "__macosx"]
            if desc["tipo"] == "mendeley":
                comprimidos = mendeley(desc, carpeta, excluir)
            elif desc["tipo"] == "zenodo":
                comprimidos = zenodo(desc, carpeta, descargas)
            elif desc["tipo"] == "dataverse":
                comprimidos = dataverse(desc, descargas)
            elif desc["tipo"] == "url":
                comprimidos = urls(desc, descargas)
            elif desc["tipo"] == "git":
                if not any(carpeta.iterdir()):
                    subprocess.run(["git", "clone", "--depth", "1", desc["url"], str(carpeta)], check=True)
                comprimidos = []
            else:
                raise RuntimeError(f"tipo desconocido {desc['tipo']}")
            for c in comprimidos:
                if c.suffix.lower() in COMPRIMIDOS:
                    descomprimir(c, carpeta)
                    if not args.guardar_comprimidos:
                        c.unlink()
            if desc.get("despues") == "coco":
                filtrar_coco(carpeta)
            (carpeta / MARCA).write_text(time.strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
            print(f"  listo: {f['nombre']}")
        except Exception as e:  # noqa: BLE001  (una fuente mala no detiene las demás)
            fallas.append((f["nombre"], str(e)))
            print(f"  FALLÓ {f['nombre']}: {e}")
    if not args.guardar_comprimidos and not fallas:
        shutil.rmtree("data/raw/descargas", ignore_errors=True)

    for f in manuales:
        print(f"\nMANUAL · {f['nombre']}: {f['descarga']['instrucciones']}\n  {f['descarga']['url']}")
        print(f"  Al terminar, crea el archivo {Path(f['carpeta']) / MARCA} (o ignóralo: preparar_datos.py no lo necesita).")
    if fallas:
        print("\nFallaron (vuelve a correr el comando; las descargas se reanudan):")
        for n, e in fallas:
            print(f"  {n}: {e}")
        sys.exit(1)
    print("\nSiguiente paso: python vision/train/preparar_datos.py --out data/prueba_carpetas  (ver GUIA-NOCHE.md)")


if __name__ == "__main__":
    main()
