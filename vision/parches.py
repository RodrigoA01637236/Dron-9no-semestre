"""Filtro de parches de hoja: va antes del clasificador.

Una foto del dron de 1920x1200 reducida a 384x384 pierde unas 5 veces el detalle, y las
lesiones tempranas desaparecen. Por eso la foto se recorre en cuadros de 384 px a
resolución nativa, con solape, como hace SAHI (Akyon et al., ICIP 2022). Los cuadros con
poca hoja se descartan con un índice de verdor (ExG) más un rango de tono amarillo, y
cada cuadro restante se clasifica por separado. El veredicto de la foto sale de los
parches: clasificar por región en lugar de por hoja completa subió en promedio 12 % la
exactitud en Barbedo (Biosystems Engineering 180, 2019).

El mismo código corta los parches para entrenar (vision/train/hacer_parches.py) y para
predecir (vision/clasificador.py), así que el modelo ve en campo lo mismo que vio al
entrenar. La guía es vision/GUIA-PARCHES.md.
"""
import math

import cv2
import numpy as np

# Valores por defecto; el JSON del modelo los puede cambiar en "parches".
CONFIG_DEFECTO = {
    "lado_px": 384,        # lado del cuadro en px de la foto original
    "lado_min_rel": 0.30,  # en fotos grandes (celular) el cuadro crece a 30 % del lado corto
    "solape": 0.20,        # 20 % de solape entre cuadros vecinos
    "min_hoja": 0.25,      # fracción mínima de hoja para que el cuadro cuente
    "min_parches": 1,      # parches seguros de una enfermedad para marcar la foto
    "top_k": 2,            # la presencia de una enfermedad es el promedio de sus k parches más altos
    "max_parches": 64,     # tope de cuadros por foto (para que no tarde de más)
    "ignorar": [],         # clases que no son hoja de plátano (p. ej. "sin_hoja")
    "separar_hojas": True, # dividir la foto en hojas y dar un veredicto por hoja
    "min_area_hoja": 0.02, # una hoja debe ocupar al menos 2 % de la foto
    "separacion_hojas": 0.08,  # distancia mínima entre centros de hojas (fracción del lado corto)
}


def config(meta_parches: dict | None) -> dict:
    cfg = dict(CONFIG_DEFECTO)
    cfg.update(meta_parches or {})
    return cfg


# ------------------------------------------------------------------ máscara de hoja

def mascara_hoja(img_bgr: np.ndarray, escala: float = 0.25) -> np.ndarray:
    """Máscara 0/1 de tejido de hoja, calculada a `escala` del tamaño para que sea rápida.

    Hoja verde: ExG = 2g - r - b sobre coordenadas cromáticas (Woebbecke et al. 1995) > 0.06.
    Clorosis y estrías amarillas: tono 15-35 en OpenCV (30-70 grados), saturación alta.
    Las manchas necróticas (café o negras) no pasan ninguno de los dos, pero el cierre
    morfológico y el relleno de huecos las recuperan cuando están dentro de la hoja. Una hoja completamente seca
    puede quedar fuera; para eso hay respaldo con la foto completa (clasificador.py).
    """
    h, w = img_bgr.shape[:2]
    chica = cv2.resize(img_bgr, (max(1, int(w * escala)), max(1, int(h * escala))),
                       interpolation=cv2.INTER_AREA)
    f = chica.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    suma = b + g + r + 1e-6
    exg = (2 * g - r - b) / suma
    hsv = cv2.cvtColor(chica, cv2.COLOR_BGR2HSV)
    tono, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    verde = (exg > 0.06) & (val > 25)
    amarillo = (tono >= 15) & (tono <= 35) & (sat > 90) & (val > 60)
    m = (verde | amarillo).astype(np.uint8)
    k = max(3, int(round(min(chica.shape[:2]) * 0.02)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    # Huecos encerrados por hoja y chicos (< 3 % de la foto) = lesiones necróticas: se rellenan.
    # Los grandes suelen ser suelo visto entre hojas y se quedan fuera.
    _, etiquetas, stats, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
    alto, ancho = m.shape
    x, y, w, h, area = stats.T
    toca_borde = (x == 0) | (y == 0) | (x + w == ancho) | (y + h == alto)
    rellenar = ~toca_borde & (area < 0.03 * alto * ancho)
    rellenar[0] = False  # etiqueta 0 = la hoja misma
    m[rellenar[etiquetas]] = 1
    return m


# ------------------------------------------------------------------ rejilla de cuadros

def _posiciones(total: int, lado: int, solape: float) -> list[int]:
    """Inicios de los cuadros sobre un eje; el último toca el borde."""
    if total <= lado:
        return [0]
    paso = lado * (1 - solape)
    n = int(math.ceil((total - lado) / paso)) + 1
    return [int(round(i * (total - lado) / (n - 1))) for i in range(n)]


def lado_cuadro(alto: int, ancho: int, cfg: dict) -> int:
    """384 px en la foto del dron; en una foto de celular de 4000x3000 crece a ~900 px,
    para que cada cuadro cubra un trozo de hoja parecido al de entrenamiento."""
    lado = max(int(cfg["lado_px"]), int(cfg["lado_min_rel"] * min(alto, ancho)))
    return min(lado, max(alto, ancho))


def cuadros(img_bgr: np.ndarray, cfg: dict, mascara: np.ndarray | None = None) -> list[dict]:
    """Lista de cuadros {x, y, w, h, hoja}. `hoja` es la fracción de hoja (0-1)."""
    alto, ancho = img_bgr.shape[:2]
    lado = lado_cuadro(alto, ancho, cfg)
    solape = float(cfg["solape"])
    xs = _posiciones(ancho, lado, solape)
    ys = _posiciones(alto, lado, solape)
    # Si hay demasiados, se agranda el paso hasta caber en max_parches.
    while len(xs) * len(ys) > int(cfg["max_parches"]) and solape > -1:
        solape -= 0.1
        xs, ys = _posiciones(ancho, lado, solape), _posiciones(alto, lado, solape)

    if mascara is None:
        mascara = mascara_hoja(img_bgr)
    esc_y, esc_x = mascara.shape[0] / alto, mascara.shape[1] / ancho
    integral = cv2.integral(mascara)  # suma acumulada: área de hoja de cualquier cuadro en O(1)

    salida = []
    for y in ys:
        for x in xs:
            w, h = min(lado, ancho - x), min(lado, alto - y)
            x0, y0 = int(x * esc_x), int(y * esc_y)
            x1 = max(x0 + 1, int(round((x + w) * esc_x)))
            y1 = max(y0 + 1, int(round((y + h) * esc_y)))
            area = (x1 - x0) * (y1 - y0)
            s = integral[y1, x1] - integral[y0, x1] - integral[y1, x0] + integral[y0, x0]
            salida.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h),
                           "hoja": round(float(s) / area, 3)})
    return salida


def recortar(img_bgr: np.ndarray, c: dict) -> np.ndarray:
    return img_bgr[c["y"]:c["y"] + c["h"], c["x"]:c["x"] + c["w"]]


# ------------------------------------------------------------------ separar hojas

def _elipse(k: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def separar_hojas(img_bgr: np.ndarray, mascara: np.ndarray, cfg: dict) -> tuple[np.ndarray, list[dict]]:
    """Divide la vegetación de la foto en hojas aproximadas (watershed sobre la forma).

    1. Los centros de las hojas son los puntos más alejados del borde de la máscara
       (transformada de distancia, suavizada).
    2. Desde cada centro se inunda la foto (watershed de OpenCV, que avanza primero por
       donde el color cambia poco): los bordes y nervaduras frenan la inundación, así dos
       hojas que se tocan quedan separadas. Lo que no es vegetación se quita al final.
    3. Dos trozos vecinos se vuelven a juntar si el paso entre ellos es casi tan ancho
       como ellos mismos (es la misma hoja, solo alargada).
    Es una aproximación: hojas muy encimadas, sin cuello entre ellas, quedan juntas.
    Devuelve el mapa de etiquetas (a la escala de la máscara; 0 = nada) y la lista de
    hojas con su caja en pixeles de la foto, de la más grande a la más chica.
    """
    alto, ancho = img_bgr.shape[:2]
    mh, mw = mascara.shape
    m = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, _elipse(3))
    if m.sum() == 0:
        return np.zeros((mh, mw), np.int32), []
    dist = cv2.GaussianBlur(cv2.distanceTransform(m, cv2.DIST_L2, 5), (0, 0), 2) * m
    k = max(5, int(min(mh, mw) * float(cfg.get("separacion_hojas", 0.08)))) | 1
    picos = (dist >= cv2.dilate(dist, _elipse(k)) - 1e-6) & (dist > max(2.0, 0.15 * float(dist.max())))
    n, centros = cv2.connectedComponents(picos.astype(np.uint8))

    # Sin marca de fondo: si el fondo compite, se mete a las hojas por sus bordes suaves.
    marcas = np.zeros((mh, mw), np.int32)
    marcas[centros > 0] = centros[centros > 0] + 1       # una marca por centro: 2..n
    chica = cv2.GaussianBlur(cv2.resize(img_bgr, (mw, mh), interpolation=cv2.INTER_AREA), (0, 0), 1)
    cv2.watershed(chica, marcas)
    marcas[(m == 0) & (marcas >= 2)] = 0

    # Juntar trozos de la misma hoja: el cruce más ancho entre dos regiones (punto de silla)
    # comparado con el centro más angosto de las dos.
    pico = np.zeros(n + 2)
    np.maximum.at(pico, np.clip(marcas, 0, None).ravel(), dist.ravel())
    union = list(range(n + 2))

    def raiz(i):
        while union[i] != i:
            union[i] = union[union[i]]
            i = union[i]
        return i

    ys, xs = np.nonzero((marcas == -1) & (m > 0))
    sillas: dict[tuple[int, int], float] = {}
    for y, x in zip(ys, xs):
        vecinos = {int(marcas[yy, xx]) for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                   if 0 <= yy < mh and 0 <= xx < mw and marcas[yy, xx] >= 2}
        if len(vecinos) == 2:
            par = tuple(sorted(vecinos))
            sillas[par] = max(sillas.get(par, 0.0), float(dist[y, x]))
    for (a, b), silla in sorted(sillas.items(), key=lambda kv: -kv[1]):
        if silla >= 0.7 * min(pico[a], pico[b]):
            union[raiz(a)] = raiz(b)
    raices = np.array([raiz(i) for i in range(n + 2)])
    etiquetas = np.where(marcas >= 2, raices[np.clip(marcas, 0, None)], 0).astype(np.int32)

    # Cada hoja se queda solo con su pedazo más grande (quita pixeles sueltos del fondo).
    for i in np.unique(etiquetas):
        if i == 0:
            continue
        nc, comp, st, _ = cv2.connectedComponentsWithStats((etiquetas == i).astype(np.uint8))
        if nc > 2:
            mayor = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            etiquetas[(comp != mayor) & (comp > 0)] = 0

    # Quitar regiones chicas y numerar por tamaño
    areas = np.bincount(etiquetas.ravel(), minlength=n + 2)
    minimo = float(cfg.get("min_area_hoja", 0.02)) * mh * mw
    orden = [i for i in np.argsort(-areas) if i > 0 and areas[i] >= minimo]
    nuevo = np.zeros(len(areas), np.int32)
    for j, i in enumerate(orden, 1):
        nuevo[i] = j
    etiquetas = nuevo[etiquetas]

    ex, ey = ancho / mw, alto / mh
    hojas = []
    for j in range(1, len(orden) + 1):
        ys, xs = np.nonzero(etiquetas == j)
        x0, x1 = int(xs.min() * ex), int(min(ancho, (xs.max() + 1) * ex))
        y0, y1 = int(ys.min() * ey), int(min(alto, (ys.max() + 1) * ey))
        hojas.append({"id": j, "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
                      "area": round(float(len(xs)) / (mh * mw), 3)})
    return etiquetas, hojas


def hoja_de_cuadro(c: dict, etiquetas: np.ndarray, alto: int, ancho: int) -> int | None:
    """La hoja que más ocupa el cuadro (si ocupa al menos 10 % de él)."""
    mh, mw = etiquetas.shape
    x0, y0 = int(c["x"] * mw / ancho), int(c["y"] * mh / alto)
    x1 = max(x0 + 1, int(round((c["x"] + c["w"]) * mw / ancho)))
    y1 = max(y0 + 1, int(round((c["y"] + c["h"]) * mh / alto)))
    sub = etiquetas[y0:y1, x0:x1]
    cuenta = np.bincount(sub.ravel())
    cuenta[0] = 0
    if len(cuenta) < 2 or cuenta.max() < 0.1 * sub.size:
        return None
    return int(cuenta.argmax())


# ------------------------------------------------------------------ veredicto de la foto

def agregar(probs: np.ndarray, clases: list[str], cfg: dict, umbral: float) -> dict:
    """Junta las probabilidades de los parches (N x C) en un veredicto.

    Regla (como lo haría un agrónomo): si al menos `min_parches` parches dicen con
    seguridad la misma enfermedad, la foto tiene esa enfermedad. Si no, la foto es sana
    solo si la hoja en promedio se ve sana.
    - Los parches cuya clase más probable está en `ignorar` (p. ej. "sin_hoja": suelo,
      cielo, otras plantas) no cuentan. Si ninguno es hoja de plátano, el veredicto es
      esa clase: "no se detectan hojas de plátano".
    - Presencia de una enfermedad = promedio de sus parches más altos: tantos como votos
      seguros tenga (al menos `min_parches`, a lo más `top_k`).
    - Puntaje de sana = promedio de P(sana) en todos los parches de hoja.
    Los puntajes no suman 1: cada uno es "qué tan seguro está de que eso aparece".
    """
    ignorar = set(cfg.get("ignorar") or [])
    n_total = probs.shape[0]
    gana_todos = probs.argmax(axis=1)
    fraccion = {c: round(float((gana_todos == i).sum()) / max(1, n_total), 3) for i, c in enumerate(clases)}
    idx_ign = [i for i, c in enumerate(clases) if c in ignorar]
    es_hoja = ~np.isin(gana_todos, idx_ign)
    if not es_hoja.any():
        medias = {clases[i]: float(probs[:, i].mean()) for i in idx_ign}
        clase = max(medias, key=medias.get)
        return {"clase": clase, "confianza": medias[clase],
                "probs": {c: float(probs[:, i].mean()) for i, c in enumerate(clases)},
                "votos": {}, "fraccion": fraccion, "n_hoja": 0}

    probs = probs[es_hoja]
    validas = [i for i, c in enumerate(clases) if c not in ignorar]
    n = probs.shape[0]
    top_k = max(1, int(cfg["top_k"]))
    min_parches = max(1, min(int(cfg["min_parches"]), n))

    gana = probs.argmax(axis=1)
    seguro = probs.max(axis=1) >= umbral

    puntajes, votos = {}, {}
    for i in validas:
        c = clases[i]
        col = np.sort(probs[:, i])[::-1]
        votos[c] = int(((gana == i) & seguro).sum())
        k = min(n, max(min_parches, min(top_k, votos[c])))
        puntajes[c] = float(col.mean() if c == "sana" else col[:k].mean())

    enfermedades = [c for c in puntajes if c != "sana"]
    marcadas = [c for c in enfermedades if votos[c] >= min_parches and puntajes[c] >= umbral]
    if marcadas:
        clase = max(marcadas, key=lambda c: (votos[c], puntajes[c]))
        confianza = puntajes[clase]
    else:
        clase = max(puntajes, key=puntajes.get)
        confianza = puntajes[clase]
        if clase in enfermedades and confianza >= umbral:
            # Seguro en pocos parches, pero menos que min_parches: no alcanza para
            # diagnosticar; queda justo bajo el umbral para que vaya a revisión humana.
            confianza = min(confianza, umbral * 0.99)
    return {"clase": clase, "confianza": float(confianza), "probs": puntajes,
            "votos": votos, "fraccion": fraccion, "n_hoja": int(n)}
