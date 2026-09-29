from ultralytics import YOLO
from pathlib import Path

# ==========================================
# RUTAS DEL PROYECTO
# ==========================================

# Carpeta donde se encuentra este programa
CARPETA_VISION = Path(__file__).parent

# Imagen que queremos analizar
IMAGENES = CARPETA_VISION / "imagenes"

# Carpeta donde guardaremos las detecciones
RESULTADOS = CARPETA_VISION / "resultados"


# ==========================================
# MODELO YOLO
# ==========================================

modelo = YOLO("yolo11n.pt")


# ==========================================
# DETECCIÓN
# ==========================================

resultados = modelo.predict(
    source=str(IMAGENES),
    device=0,
    conf=0.50,
    save=True,
    project=str(RESULTADOS),
    name="deteccion",
    exist_ok=True
)


# ==========================================
# MOSTRAR RESULTADOS
# ==========================================

print("\n--- OBJETOS DETECTADOS ---")

total = 0

for resultado in resultados:

    for caja in resultado.boxes:

        clase_id = int(caja.cls[0])
        confianza = float(caja.conf[0])

        nombre = resultado.names[clase_id]

        total += 1

        print(
            f"{total}. {nombre} | "
            f"Confianza: {confianza:.2%}"
        )


print(f"\nTotal de objetos detectados: {total}")
print(f"Imagen procesada guardada en: {RESULTADOS / 'deteccion'}")