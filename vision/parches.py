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
    "ignorar": [],         # clases que no son hoja (p. ej. "fondo")
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


# ------------------------------------------------------------------ veredicto de la foto

def agregar(probs: np.ndarray, clases: list[str], cfg: dict, umbral: float) -> dict:
    """Junta las probabilidades de los parches de hoja (N x C) en un veredicto.

    Regla (como lo haría un agrónomo): si al menos `min_parches` parches dicen con
    seguridad la misma enfermedad, la foto tiene esa enfermedad. Si no, la foto es sana
    solo si la hoja en promedio se ve sana.
    - Presencia de una enfermedad = promedio de sus parches más altos: tantos como votos
      seguros tenga (al menos `min_parches`, a lo más `top_k`).
    - Puntaje de sana = promedio de P(sana) en todos los parches de hoja.
    Los puntajes no suman 1: cada uno es "qué tan seguro está de que eso aparece".
    """
    ignorar = set(cfg.get("ignorar") or [])
    validas = [i for i, c in enumerate(clases) if c not in ignorar]
    n = probs.shape[0]
    top_k = max(1, int(cfg["top_k"]))
    min_parches = max(1, min(int(cfg["min_parches"]), n))

    gana = probs.argmax(axis=1)
    seguro = probs.max(axis=1) >= umbral

    puntajes, votos, fraccion = {}, {}, {}
    for i in validas:
        c = clases[i]
        col = np.sort(probs[:, i])[::-1]
        votos[c] = int(((gana == i) & seguro).sum())
        k = min(n, max(min_parches, min(top_k, votos[c])))
        puntajes[c] = float(col.mean() if c == "sana" else col[:k].mean())
        fraccion[c] = round(float((gana == i).sum()) / n, 3)

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
            "votos": votos, "fraccion": fraccion}
