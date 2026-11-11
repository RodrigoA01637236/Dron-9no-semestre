"""Rasgos de la penúltima capa del clasificador y filtro "¿esto es hoja de plátano?".

El modelo termina en: rasgos (1280 números por imagen) -> una capa lineal -> softmax.
`con_rasgos` agrega al .onnx una salida más con esos rasgos (mismo modelo, mismos pesos),
editando el protobuf directamente para no depender del paquete onnx (la Jetson solo tiene
onnxruntime). Es la misma edición que hace web/motor.js en el navegador.

Filtro de hoja (`filtro_hoja` en el JSON del modelo): una sonda lineal sobre esos rasgos que
separa hoja de plátano de objetos cotidianos. Hace falta porque la clase "sin_hoja" se entrenó
con otras plantas, frutos y fondos de cultivo, nunca con una mesa, una mano o una taza, y ante
eso el modelo elige una clase de hoja con mucha seguridad. Un cuadro con puntaje menor que el
umbral cuenta como "sin_hoja" (probabilidad 1). Se entrena con vision/train/filtro_hoja.py.
"""
from __future__ import annotations

import numpy as np


def _varint(buf: bytes, p: int) -> tuple[int, int]:
    x, s = 0, 0
    while True:
        b = buf[p]
        p += 1
        x |= (b & 0x7F) << s
        s += 7
        if not b & 0x80:
            return x, p


def _campos(buf: bytes, ini: int, fin: int) -> list[tuple[int, int, int, int, int]]:
    """Campos de un mensaje protobuf: (número, tipo, inicio de la clave, inicio, fin del valor)."""
    lista, p = [], ini
    while p < fin:
        k0 = p
        k, p = _varint(buf, p)
        campo, tipo = k >> 3, k & 7
        if tipo == 0:
            a = p
            _, p = _varint(buf, p)
            b = p
        elif tipo == 1:
            a, b = p, p + 8
            p = b
        elif tipo == 5:
            a, b = p, p + 4
            p = b
        elif tipo == 2:
            n, a = _varint(buf, p)
            b = p = a + n
        else:
            raise ValueError("protobuf con un tipo inesperado")
        lista.append((campo, tipo, k0, a, b))
    return lista


def _codificar(x: int) -> bytes:
    o = bytearray()
    while x > 127:
        o.append((x & 127) | 128)
        x >>= 7
    o.append(x)
    return bytes(o)


def _largo(campo: int, datos: bytes) -> bytes:
    return _codificar(campo * 8 + 2) + _codificar(len(datos)) + datos


def _entero(campo: int, v: int) -> bytes:
    return _codificar(campo * 8) + _codificar(v)


def con_rasgos(datos: bytes) -> tuple[bytes, str, np.ndarray, np.ndarray]:
    """(onnx con la salida extra, nombre de esa salida, pesos K x D y sesgo K de la última capa)."""
    grafo = next(c for c in _campos(datos, 0, len(datos)) if c[0] == 7 and c[1] == 2)
    en_grafo = _campos(datos, grafo[3], grafo[4])

    def texto(c):
        return datos[c[3]:c[4]].decode("utf-8")

    # NodeProto: entradas en el campo 1, tipo de operación en el 4. La capa es el último Gemm.
    gemms = []
    for c in en_grafo:
        if c[0] == 1 and c[1] == 2:
            nodo = _campos(datos, c[3], c[4])
            if any(x[0] == 4 and texto(x) == "Gemm" for x in nodo):
                gemms.append(nodo)
    if not gemms:
        raise ValueError("no encontré la última capa")
    rasgos, peso, sesgo = [texto(x) for x in gemms[-1] if x[0] == 1][:3]

    def leer(nombre):  # TensorProto float guardado en raw_data
        for c in en_grafo:
            if c[0] != 5:
                continue
            t = _campos(datos, c[3], c[4])
            n = next((x for x in t if x[0] == 8), None)
            if n and texto(n) == nombre:
                r = next(x for x in t if x[0] == 9)
                return np.frombuffer(datos[r[3]:r[4]], dtype="<f4").copy()
        raise ValueError("no encontré " + nombre)

    b = leer(sesgo)
    W = leer(peso).reshape(len(b), -1)
    # Salida [n, D]: n libre, porque el v2 revisa varios cuadros a la vez.
    forma = _largo(2, _largo(1, _largo(2, b"n")) + _largo(1, _entero(1, W.shape[1])))
    salida = _largo(12, _largo(1, rasgos.encode("utf-8")) + _largo(2, _largo(1, _entero(1, 1) + forma)))
    nuevo = datos[grafo[3]:grafo[4]] + salida
    return (datos[:grafo[2]] + _codificar(7 * 8 + 2) + _codificar(len(nuevo)) + nuevo + datos[grafo[4]:],
            rasgos, W, b)


def color_hoja(x_chw: np.ndarray) -> float:
    """Fracción de pixeles con color de hoja (verde, o amarillo saturado de clorosis y halos de
    lesión) en un cuadro ya preparado para el modelo (3 x L x L, RGB, 0-1), mirando uno de cada
    4 x 4. Misma cuenta que colorHoja() en web/motor.js."""
    r, g, b = (x_chw[:, ::4, ::4].astype(np.float32) * 255)
    mx = np.maximum(np.maximum(r, g), b)
    d = mx - np.minimum(np.minimum(r, g), b) + 1e-6
    s = np.where(mx > 0, (d - 1e-6) / (mx + 1e-6), 0)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    verde = (h >= 60) & (h <= 190) & (s >= 0.2) & (mx >= 40)
    amarillo = (h >= 36) & (h < 60) & (s >= 0.39) & (mx >= 80)
    return float((verde | amarillo).mean())


class FiltroHoja:
    """Sonda lineal: puntaje = w · rasgos + b. Debajo del umbral, el cuadro no es hoja de plátano.

    Dos umbrales: uno estricto para cuadros casi sin color de hoja (una mesa, una mano, una
    pared) y otro permisivo para cuadros verdes o amarillos, para no rechazar hojas de fotos
    distintas a las de entrenamiento (otro celular, otra altura de vuelo)."""

    def __init__(self, meta: dict, dim: int):
        f = meta.get("filtro_hoja") or {}
        self.w = np.asarray(f.get("w", []), dtype=np.float32)
        self.b = float(f.get("b", 0.0))
        self.umbral = float(f.get("umbral", 0.0))
        self.umbral_verde = float(f.get("umbral_verde", self.umbral))
        self.verde_min = float(f.get("verde_min", 1.01))
        if self.w.shape != (dim,):
            raise ValueError(f"filtro_hoja trae {self.w.size} pesos y el modelo da {dim} rasgos")

    def puntajes(self, rasgos: np.ndarray) -> np.ndarray:
        return rasgos.astype(np.float32) @ self.w + self.b

    def es_hoja(self, rasgos: np.ndarray, color: np.ndarray) -> np.ndarray:
        umbral = np.where(np.asarray(color) >= self.verde_min, self.umbral_verde, self.umbral)
        return self.puntajes(rasgos) >= umbral
