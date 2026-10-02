"""Entrenamiento local del clasificador de Sigatoka (transfer learning).

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/train_cls.py --data data/dataset --epochs 50 --imgsz 384 --batch 32

Sin GPU: --batch 16 --workers 2 (y deja la corrida de noche).
Al terminar: registra la corrida en vision/train/experiments.md y respalda
runs/classify/<run>/weights/{best.pt,best.onnx} en Drive.
Ver vision/GUIA-MODELO.md fase 3.
"""
import argparse

from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="carpeta dataset/ con train/ val/ test/")
    ap.add_argument("--model", default="yolov8n-cls.pt", help="pesos base (ImageNet)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=384)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    model = YOLO(args.model)

    # Aumentado del dominio dron (doc 06 §3): rotaciones leves, escala, volteo
    # horizontal y brillo; SIN volteo vertical ni cambios fuertes de tono — el
    # color amarillo/marrón de las lesiones es señal diagnóstica.
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        patience=10,
        augment=True,
        degrees=10,
        scale=0.5,
        fliplr=0.5,
        flipud=0.0,
        hsv_h=0.005,
        hsv_s=0.3,
        hsv_v=0.4,
    )

    # Evaluar SIEMPRE en test; las métricas de val no se reportan como finales.
    metrics = model.val(split="test")
    print(f"top1 (test): {metrics.top1:.4f}")
    print("Matriz de confusión y curvas en runs/classify/<run>/")

    # Exportar el paquete modelo: entrada del pipeline de la Jetson (doc 07).
    onnx_path = model.export(format="onnx", imgsz=args.imgsz, opset=17)
    print(f"ONNX exportado: {onnx_path}")

    # Orden EXACTO de clases para el campo "classes" del JSON de metadata
    # (fase 5 de la guía): un orden equivocado cruza los diagnósticos.
    print(f"model.names (orden de salida): {model.names}")


if __name__ == "__main__":
    main()
