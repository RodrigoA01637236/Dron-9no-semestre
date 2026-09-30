# Chuleta de comandos — sistema de visión (PowerShell)

## 🔑 Ritual de inicio (SIEMPRE, cada vez que abras una terminal)

```powershell
& $env:USERPROFILE\venvs\dron-vision\Scripts\Activate.ps1
cd $env:USERPROFILE\Documents\Dron-9no-semestre
git pull
```

Sabes que estás listo cuando la línea se ve así:
`(dron-vision) PS C:\Users\<tu-usuario>\Documents\Dron-9no-semestre>`

---

## 🎬 Demos (para presentar)

```powershell
# Demo con fotos: arrastra imágenes y las diagnostica (se abre en el navegador)
python vision\demo.py

# Demo en TIEMPO REAL con la webcam (q = salir, g = guardar captura en runs\live\)
python vision\demo_live.py
# si la cámara no abre:  python vision\demo_live.py --camara 1
```

Fotos de prueba que el modelo nunca vio (para arrastrar a la demo):
```powershell
explorer data\dataset\test
```

Truco de presentación: busca "sigatoka banana leaf" en el celular y apunta la
webcam a la pantalla del celular.

---

## 🧠 Entrenamiento y evaluación

```powershell
# Reorganizar el dataset desde las carpetas descargadas (solo si cambian los datos)
python scripts\make_splits.py --src "data\raw\public\banana" --out data\dataset

# Entrenar (RTX 4060: ~20-35 min). Al final imprime top1 y model.names
python vision\train\train_cls.py --data data\dataset --epochs 50 --imgsz 384 --batch 32

# Ver las imágenes que el modelo falla (las copia a runs\errores\)
python vision\train\find_errors.py

# Verificar el paquete ONNX contra una carpeta del test
python vision\verificar_onnx.py --carpeta data\dataset\test\sigatoka
```

Después de cada entrenamiento: registrar la corrida en `vision\train\experiments.md`,
copiar el nuevo `best.onnx` a `vision\models\` y respaldar pesos a Drive.

Resultados y gráficas del último entrenamiento: `explorer runs\classify\train`

---

## 📤 Subir tus cambios a GitHub

```powershell
git add <archivos>
git commit -m "mensaje corto de qué hiciste"
git push
```

Si el push dice **"rejected / fetch first"** → `git pull` y luego `git push` otra vez.
Si el pull abre VS Code pidiendo un mensaje de merge → guarda y cierra la pestaña.

---

## 🚑 Problemas frecuentes

| Síntoma | Causa | Arreglo |
|---|---|---|
| `python`/`pip`/`kaggle` "is not recognized" | Falta activar el venv | Ritual de inicio, paso 1 |
| `fatal: not a git repository` | Estás en la carpeta equivocada | Ritual de inicio, paso 2 |
| `torch.cuda.is_available()` = False | PyTorch sin CUDA | `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128` (tras `pip uninstall -y torch torchvision`) |
| La terminal "se congela" instalando o copiando | Está trabajando en silencio | Espera; checa el disco/GPU en el Administrador de Tareas |
