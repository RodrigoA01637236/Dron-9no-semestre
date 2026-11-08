# Technical enablers: low-cost model and software upgrades for a community Black Sigatoka detection system

Context assumed throughout: fixed hardware (Jetson Orin Nano 8GB, ZED X Mini, Pixhawk 6C/HERE4), YOLOv8n-cls ONNX at 384x384 with classes otra_condicion/sana/sigatoka and a 0.65 confidence threshold, an offline Flask ground station, and a Mexican deployment context (the repo docs mention Chiapas, Tabasco, Veracruz and Colima). Research date: November 2026. Ultralytics docs have moved on to YOLO26 and a new `quantize` export argument; YOLOv8 checkpoints still export through the same API.

## 1. Running the same model on cheap Android phones and in the browser, fully offline

### Takeaway
The team already has an ONNX model, so the cheapest route to "same model on any phone" is ONNX Runtime Web (WASM with optional WebGPU) inside an installable PWA served by the existing Flask app. A native LiteRT (TFLite) app is a second-tier option. INT8 post-training quantization cuts size about 4x, but it can cost 5 to 8 top-1 points on small MobileNet-class CNNs and may not speed them up. Any quantized build has to pass the team's held-out field exam before it ships, and its threshold has to be re-chosen.

### Cited Findings
- **Baseline cost of YOLOv8n-cls.** 2.7M params, 4.3B FLOPs, 12.9 ms CPU ONNX and 0.31 ms A100 TensorRT, at 224 px. Top-1 on ImageNet is listed as 69.0% (older mirrors show 66.6%). The FLOPs column is labelled "at 640", which conflicts with the 224 input. — [Ultralytics YOLOv8 docs](https://docs.ultralytics.com/models/yolov8/); older figure in [HF mirror of classify.md](https://huggingface.co/spaces/chelseat2023/yolov8/blob/main/docs/en/tasks/classify.md)
- **Current Ultralytics export targets** include `onnx`, `engine` (TensorRT), `litert` (TFLite), `edgetpu`, `saved_model`, `openvino`, `coreml`, `mnn`, `ncnn` and `executorch`.
  - `half`/`int8` are deprecated in favour of `quantize` (16 = FP16; 8 = INT8 PTQ, which needs calibration `data`/`fraction`).
  - LiteRT also accepts `w8a16`, which uses calibration data, and `w8a32`, which is "dynamic INT8 (no calibration)".
  - For classification, `data` can be a dataset directory.
  - TF.js does not appear on the current export page.
  - `results[0].probs` is already softmaxed.
  - Source: [Ultralytics Export mode](https://docs.ultralytics.com/modes/export/)
- **LiteRT/TFLite quantization trade-offs**, measured on a Pixel 2 with a single big core. PTQ = post-training quantization; QAT = quantization-aware training.

  | Model | Top-1: float / PTQ / QAT | Latency: float / PTQ / QAT | Size |
  |---|---|---|---|
  | MobileNet-v1 | 0.709 / 0.657 / 0.70 | 124 / 112 / 64 ms | 16.9 MB to 4.3 MB |
  | MobileNet-v2 | 0.719 / 0.637 / 0.709 | 89 / **98** / 54 ms | 14 MB to 3.6 MB |

  On MobileNet-v2, PTQ was slower than float. Larger models (Inception_v3, ResNet_v2_101) lose under 1 point with PTQ. Float16 PTQ cuts size up to 50% (CPU/GPU); dynamic-range and full-integer cut it up to 75%. — [LiteRT model optimization](https://developers.google.com/edge/litert/models/model_optimization)
- **XNNPACK.** Google reports TFLite gains most from the XNNPACK backend "on small neural network models and low-end mobile phones". Devices can be measured with `benchmark_model --use_xnnpack=true`. — [TensorFlow blog, XNNPACK integration](https://blog.tensorflow.org/2020/07/accelerating-tensorflow-lite-xnnpack-integration.html?hl=es)
- **Budget-phone proxy.** A Moto G Power 5G (Dimensity 7020) ran YOLOv8n *detection* INT8 at about 77 ms with XNNPACK CPU+NEON, and 75 to 117 ms via NNAPI/GPU shim (median of 5 runs after warm-up). This is a third-party, non-authoritative source. — [nx_tflite_mob README](https://hexdocs.pm/nx_tflite_mob/readme.md)
- **Board proxy.** On a Raspberry Pi 4 (Cortex-A72), MobileNetV2 ran at 23 ms average in TFLite vs 41 ms in PyTorch Mobile (26 ms with XNNPACK). Single blog test. — [DEV Community](https://dev.to/tildalice/tensorflow-lite-vs-pytorch-mobile-cortex-a-latency-test-1nb9)
- **ONNX Runtime Web backends.**
  - Backends: `wasm` (alias `cpu`), `webgpu`, `webgl` and `webnn`.
  - "All ONNX operators are supported by WASM but only a subset are currently supported by WebGL, WebGPU and WebNN".
  - Models can be converted to ORT format for smaller binary size, faster init and lower peak memory, and a custom build can shrink the runtime.
  - Source: [ONNX Runtime Web tutorial](https://onnxruntime.ai/docs/tutorials/web/)
- **ONNX Runtime Web packaging.**
  - The default binary is `ort-wasm-simd-threaded.wasm`; `ort-wasm-simd-threaded.jsep.wasm` adds WebGPU/WebNN.
  - Self-hosting is supported: files are found relative to the JS bundle or through `ort.env.wasm.wasmPaths`.
  - Importing `onnxruntime-web/wasm` alone reduces size.
  - Source: [ORT Web deploy docs](https://onnxruntime.ai/docs/tutorials/web/deploy.html)
- **WebGPU in practice** (blog-level sources).
  - Support is Chrome/Edge 113+; Firefox and Safari are experimental.
  - The recommended setup is `executionProviders: ['webgpu','wasm']` so it falls back to CPU.
  - The first inference compiles shaders (50 to 200 ms), so benchmarks should exclude warm-up.
  - Published speedup claims (10 to 50x) have no stated method.
  - Sources: [Mintlify ORT WebGPU page](https://www.mintlify.com/microsoft/onnxruntime/execution-providers/webgpu), [Medium guide](https://medium.com/@Modexa/8-webgpu-onnx-runtime-web-inference-guides-4220cff29ad8), [SitePoint](https://www.sitepoint.com/webgpu-vs-webasm-transformers-js/)
- **Secure contexts.** Web Share (`navigator.share`/`canShare`) works only in secure contexts (HTTPS) and needs user activation. — [MDN Navigator.share](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share)
- **Service workers** (the PWA offline cache) only run over HTTPS, with localhost as the development exception. — [MDN Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

### Inferences
- **Lowest-effort path.** Effort about 1 to 2 days, $0, high expo impact.
  - Add an `/app` PWA page to Flask that loads `onnxruntime-web` (WASM build), the existing `.onnx`, a manifest, and a service worker that pre-caches the HTML/JS/WASM/model.
  - Preprocess the camera or file image to 384x384 RGB, normalised like Ultralytics, in a `<canvas>`, then run the session. No model conversion is needed.
  - A YOLOv8n-cls ONNX is about 10 MB FP32 (2.7M params x 4 bytes), roughly 5 MB as FP16 or 3 MB as INT8, which suits a one-time cache.
- **Secure-context gotcha.** A phone opening `http://192.168.x.x:5000` is not a secure context, so the service worker and Web Share will not work.
  - Option 1: serve the laptop over HTTPS with a locally trusted cert (e.g., mkcert), so phones must trust that CA.
  - Option 2: host the static PWA once on any free HTTPS static host so phones install it, after which it works offline and needs no laptop.
- **Input size on phones.** At 384 px, compute is about (384/224)^2 ≈ 2.9x the 224 px figure. Expect roughly tens of ms in WASM on a mid-range phone and more on low-end ones (rough estimate from the proxies above; not measured). Training a 224 or 256 px variant for phones is a cheap A/B against the field exam.
- **Quantization order on phones.** Try FP16 first. Then dynamic INT8 (`w8a32`) or ORT `quantize_dynamic`. Use full INT8 PTQ only if it passes the held-out field exam. If INT8 loses accuracy, QAT (`quantize=8` at train time in current Ultralytics) is the documented fix.
- **Threshold after quantization.** Re-derive the 0.65 threshold for each export, because quantization shifts confidences (also stated for TensorRT; see Q2).
- **Native app.** A LiteRT/TFLite Android app (Kotlin + LiteRT + XNNPACK delegate) is more work (1 to 2 weeks) and mainly buys camera control and NNAPI/GPU delegates. For an expo the PWA demonstrates "runs on any phone, no install, offline" more convincingly.

### Gaps
- I found no rigorous public benchmark of a YOLOv8n-cls (or similar 2.7M-param CNN) on a sub-$150 Android phone under ORT Web WASM vs WebGPU vs TFLite. The team should measure it themselves with the TFLite `benchmark_model` tool and a JS timing harness.
- I found no ORT Web binary-size figures in the official docs.
- I could not confirm whether Ultralytics still supports `format="tfjs"`; it is absent from the current export page.

## 2. Jetson acceleration (TensorRT FP16/INT8) on Orin Nano 8GB

### Takeaway
There are two free, hardware-neutral speedups. First, enable "Super" mode (a JetPack software update that raises the Orin Nano 8GB from 40 to 67 INT8 TOPS). Second, move inference from CPU onnxruntime to the GPU: TensorRT FP16, or onnxruntime-gpu with the CUDA/TensorRT EP. On Orin-class boards TensorRT FP16 is roughly 3.4x faster than ONNX with no accuracy loss. INT8 adds a little more speed but measurably lowers accuracy and shifts confidences.

### Cited Findings
- **Ultralytics Jetson Orin Nano Super benchmark** (Ultralytics 8.4.33, 640 px YOLO26 detection, excludes pre/post-processing).

  | Format | Latency (ms) | mAP50-95 |
  |---|---|---|
  | PyTorch | 15.60 | 0.479 |
  | ONNX | 15.76 | 0.476 |
  | TensorRT FP32 | 7.53 | 0.477 |
  | **TensorRT FP16** | **4.57** | 0.480 |
  | TensorRT INT8 | 3.80 | **0.449** |
  | NCNN | 47.50 | 0.481 |
  | TF Lite | 286.00 | 0.476 |

  The page does not state which YOLO26 size the row is for. — [Ultralytics NVIDIA Jetson guide](https://docs.ultralytics.com/guides/nvidia-jetson/)
- **Same guide, setup notes.**
  - Use `sudo nvpmodel -m 0` (max power) and `sudo jetson_clocks`, and monitor with `jtop` (jetson-stats).
  - Engines are device-specific and must be validated on the deployment device.
  - For JetPack 6 / Python 3.10 it supplies prebuilt `onnxruntime-gpu` 1.23.0/1.20.0 wheels.
  - Keep TensorRT 10.x on JetPack 6/7.
  - DLA export example: `model.export(format="engine", device="dla:0", quantize=16)`; DLA supports FP16/INT8 only.
  - Source: [Ultralytics NVIDIA Jetson guide](https://docs.ultralytics.com/guides/nvidia-jetson/)
- **TensorRT export arguments.** `quantize=16` (FP16) or `quantize=8` (INT8 PTQ), plus `data`, `fraction`, `workspace`, `dynamic`, `batch` and `imgsz`.
  - INT8 calibration uses MINMAX for GPU and ENTROPY_CALIBRATION_2 for DLA. Use "at least 500 calibration images that are representative", and calibrate on the target device.
  - Small batches give inaccurate scaling.
  - INT8 "can also shift confidence values, so choose the threshold from the INT8 model's own F1 curve".
  - Source: [Ultralytics TensorRT integration](https://docs.ultralytics.com/integrations/tensorrt/)
- **Same page, YOLOv8n on Jetson Orin NX 16GB** (JetPack 6.0, TensorRT 10.0.1):

  | Precision | Latency (ms) | mAP50-95 |
  |---|---|---|
  | FP32 | 6.17 | 0.37 |
  | FP16 | 3.19 | 0.37 |
  | INT8 | 2.32 | 0.32 |

  Source: [Ultralytics TensorRT integration](https://docs.ultralytics.com/integrations/tensorrt/)
- **Third-party Orin Nano YOLO11 table** (model size unstated; treat as unverified): PyTorch 21.3 ms, TorchScript 13.4, TensorRT FP16 4.91, TensorRT INT8 3.91. — [CamThink NeoEdge wiki](https://camthink-ai.github.io/wiki-documents/en/docs/NeoEdge%20NG4500%20Series/Application%20Guide/Object%20Detection)
- **Official DeepStream guide, YOLOv8s on Orin NX 16GB:** FP32 15.63 ms (64 FPS), FP16 7.94 ms (126 FPS), INT8 5.53 ms (181 FPS). — [Ultralytics DeepStream on Jetson](https://docs.ultralytics.com/guides/deepstream-nvidia-jetson)
- **Super mode.**
  - Raises the Orin Nano 8GB from 40 to 67 INT8 TOPS, with memory bandwidth up to 102 GB/s and CPU clock from 1.5 to 1.7 GHz.
  - Delivered as a software update (JetPack 6.1 rev.1 image per NVIDIA; other sources say JetPack 6.2).
  - Adds 15W, 25W and MAXN SUPER power modes.
  - NVIDIA's "1.7x" headline is for generative AI; measured LLM gains were 1.37 to 1.63x.
  - Sources: [NVIDIA dev blog](https://developer.nvidia.com/blog/?p=93942), [Tom's Hardware](https://tomshardware.com/tech-industry/artificial-intelligence/nvidia-launches-new-usd249-ai-development-board-that-does-67-tops), [Stereolabs Orin Nano Super + ZED](https://stereolabs.com/blog/getting-started-with-nvidia-orin-nano-super-and-zed), [electronicspecifier](https://electronicspecifier.com/industrial/jetson-orin-super-mode-nvidia-performance-boost-for-syslogic-rugged-computers)

### Inferences
- **Recommended Jetson change.** Effort about half a day, $0.
  - Flash or upgrade to the JetPack 6.2-era image with Super mode and set MAXN SUPER/25W while flying.
  - Run `yolo export model=best.pt format=engine quantize=16 imgsz=384` on the Jetson itself.
  - Load the `.engine` via Ultralytics, or keep the ONNX and switch onnxruntime to `onnxruntime-gpu` with `TensorrtExecutionProvider`/`CUDAExecutionProvider`.
  - Expected gain from CPU ONNX to GPU TensorRT FP16 is probably several-fold (≥3x by analogy with the ONNX vs TRT FP16 rows above). It also frees the CPU for MJPEG encoding and ZED SDK work. This is an inference; classification at 384 px was not benchmarked in the sources.
- **Skip INT8 on the Jetson.** FP16 is already far below camera frame time, and INT8 costs accuracy (detection mAP drops 0.37 to 0.32 and 0.480 to 0.449 above). A 3-class model with a confidence threshold is especially sensitive to INT8's confidence shift.
- **Spend the headroom instead on:** (a) test-time augmentation (e.g., flip + 2 crops averaged), (b) tiling a frame into several leaf-sized crops, and (c) running a second OOD/"is this a leaf" head or a segmentation model (Q3/Q4).
- **Expo demo.** Show a live FPS counter and `jtop` power draw while switching CPU-ONNX vs TensorRT-FP16 on the same video stream.

### Gaps
- No source benchmarked a YOLOv8-cls model (or any classification model) on Orin Nano with TensorRT; all numbers above are detection models at 640 px.
- The exact JetPack minimum for Super mode is inconsistent across sources (6.1 rev.1 vs 6.2).

## 3. Robustness to field and drone images with little data (active learning, semi-supervised learning, TTA, calibration, OOD, open-set, few-shot)

### Takeaway
The highest value-per-effort upgrades are post-hoc and need no new data:
- Temperature scaling, fitted on the field-exam split, makes the 0.65 threshold mean something.
- An energy-score or max-softmax OOD gate on the logits, plus a few hundred "not a banana leaf" outlier images, gives the "otra_condicion" class a principled "I don't know / retake photo" path.
- The existing uncertainty-first review queue already is active learning; published plant studies show uncertainty sampling beats random under a fixed labelling budget.
- Pseudo-labelling (FixMatch-style self-training) on the many unlabelled drone frames is the next step.

### Cited Findings
- **Active learning in plant imaging.** On soybean leaf stress/disease and weed datasets, DBAL, Entropy, Least-Confidence and Coreset acquisition all outperformed random sampling under a fixed labelling budget. The authors also note random sampling remains a reasonable baseline in some settings. — [Nagasubramanian et al., Plant Phenome Journal 2021 (NSF PAR copy)](https://par.nsf.gov/servlets/purl/10319256); [DOAJ record](https://doaj.org/article/1ce4128f51e34cfa91aaea434685c8f2)
- **Segmentation.** A Plant Phenomics 2022 study benchmarked four uncertainty-based strategies for plant organ segmentation and reports reduced annotation cost. — [PMC8897744](https://pmc.ncbi.nlm.nih.gov/articles/PMC8897744)
- **FixMatch.** Keeps pseudo-labels only when the prediction on a weakly augmented image is high-confidence, and trains on strongly augmented views. CIFAR-10 reached 94.93% with 250 labels and 88.61% with 40 labels (4 per class). — [FixMatch, arXiv 2001.07685](https://arxiv.org/abs/2001.07685v1)
- **Variance at very low label counts.** Results become highly variable at 40 labels, depending on which samples are labelled. — [FixMatch oversampling analysis, arXiv 2201.00604](https://arxiv.org/pdf/2201.00604)
- **Agricultural SSL analogue.** FixMatch-based weed (sedge) detection reached F1 98.1% with 100 labelled images and 98.2% with 200. — [Semi-supervised sedge detection](https://jolly-albattani-af3d57.netlify.app/archive/publication/Semi-supervised%20learning%20for%20detection%20of%20sedges%20in%20sod%20farms.pdf)
- **Few-shot.** A Siamese-network approach on PlantVillage reached a median of 55.5% accuracy with 1 image per class, 80.0% with 15 and 90.0% with 80. — [Tecnalia few-shot plant disease](https://scienceportal.tecnalia.com/en/publications/few-shot-learning-approach-for-plant-disease-classification-using-2/)
- **Calibration.**
  - Modern deep nets are poorly calibrated, and depth, width, weight decay and BatchNorm affect calibration.
  - Temperature scaling (one scalar T dividing the logits, fitted on a validation set) was often the most effective post-hoc method, and it does not change accuracy because the argmax is preserved.
  - ECE is computed over M equal-width confidence bins.
  - Source: [Guo et al., ICML 2017, arXiv 1706.04599](https://ar5iv.arxiv.org/html/1706.04599)
- **OOD energy score.**
  - The energy score E(x) = −T·logsumexp(logits/T) reduced average FPR at 95% TPR by 18.03% vs the softmax confidence score on a CIFAR-10 WideResNet (51.04% to 33.01%).
  - With energy fine-tuning using outlier exposure, FPR95 fell to 3.32% vs 8.53% for softmax fine-tuning.
  - Source: [Liu et al., NeurIPS 2020, arXiv 2010.03759](https://arxiv.org/abs/2010.03759v4)
- **Plant-disease open-set and OOD.** On 8 strawberry diseases, open-set recognition (OpenMatch) needed outlier exposure to work well on fine-grained plant disease. After modified training, both OpenMatch and a two-head OOD network exceeded 90% accuracy. Unknown-disease detection is framed as a prerequisite for continual learning. — [Jiang et al., Frontiers in Plant Science 2022](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9520169/)
- **Fine-tuning paradigm.** Across five plant-disease datasets, visual prompt tuning beat full fine-tuning and linear probing for OOD detection, especially with few shots. Venue/year not confirmed. — [Dong et al., JBNU portal](https://pure.jbnu.ac.kr/en/publications/the-impact-of-fine-tuning-paradigms-on-unknown-plant-diseases-rec/)
- **Probability outputs.** Ultralytics classification `probs` are already softmax probabilities; do not softmax twice. — [Ultralytics Export mode](https://docs.ultralytics.com/modes/export/)

### Inferences
Menu, in implementation order:

| Technique | Effort | Cost | Expected benefit | How |
|---|---|---|---|---|
| Temperature scaling + reliability diagram/ECE on field exam | 2 to 4 h | $0 | Honest confidences; the 0.65 threshold becomes a meaningful, documented operating point; expo-friendly reliability plot | Export logits (or take log of `probs`), fit T by minimising NLL on the held-out field split (scipy `minimize_scalar`), store T with each model version, apply in Flask/JS before thresholding |
| Selective prediction ("abstain") with a coverage-accuracy curve | 2 h | $0 | Shows accuracy on auto-accepted images vs the share sent to the human queue | Sweep the threshold on the calibrated field exam and plot accuracy vs coverage; pick a threshold for a target, e.g., ≥95% precision on "sigatoka" |
| OOD gate (max-softmax baseline + energy score) | 0.5 to 1 day | $0 | Rejects sky, soil, people, non-banana plants and blurry frames instead of forcing one of 3 classes | Compute energy from logits; set the threshold at 95% TPR on in-distribution validation; add a "No es hoja de plátano / repetir foto" UI state |
| Outlier exposure / explicit `no_hoja` class | 1 to 2 days | $0 | Bigger OOD gains (cf. 8.53% to 3.32% FPR95 with fine-tuning) | Add 300 to 1,000 non-leaf / other-crop / ground frames from the drone's own footage to training, as an extra class or as an OE loss |
| Test-time augmentation | 2 h | $0 | Usually small accuracy and calibration gains; the GPU headroom from TensorRT pays for it | Average softmax over original + horizontal flip + 2 to 4 crops; also use TTA disagreement as an extra uncertainty score for the queue |
| Uncertainty-first active learning (already built) made explicit | 0.5 day | $0 | Fewer labels for the same accuracy, per plant AL studies | Rank by entropy or margin, de-duplicate near-identical drone frames (embedding cosine or pHash) so a batch is not 20 copies of one leaf, and log a "labels vs field-exam accuracy" learning curve per model version |
| Self-training / FixMatch-lite | 2 to 5 days | $0 (GPU time on laptop/Colab) | Uses thousands of unlabelled drone frames; strongest when labelled data is scarce | Pseudo-label frames with calibrated p≥0.95 and add them with strong augmentation; never add pseudo-labels to the field exam; cap per-class counts to avoid imbalance |
| Few-shot for new conditions (e.g., Yellow Sigatoka, Moko, nutrient deficiency) | 2 to 3 days | $0 | Adds "known unknowns" without retraining the backbone | Nearest-class-mean/prototype classifier on YOLOv8-cls penultimate embeddings, with 15 to 80 examples per new class (cf. 80 to 90% Siamese results) |

- **Domain-shift augmentation for drone vs handheld images.** Motion blur, JPEG re-compression, downscale-then-upscale, colour jitter for overcast/strong sun, random perspective. These are cheap Ultralytics/Albumentations settings. Evaluate them per capture source (drone vs phone) in the field exam (inference).
- **Stratify the held-out field exam** by farm, date and device so improvements are not leakage from the same plant appearing in train and test (inference).

### Gaps
- I found no published active-learning, FixMatch or OOD study specific to Black Sigatoka or banana; the cited results are on other crops or generic benchmarks.
- I found no TTA magnitude figures for plant disease classification in the time available.
- ECE values from Guo et al. were not retrieved.

## 4. Moving from classification to localization and severity, plus explanations for farmers

### Takeaway
A credible upgrade path has four steps:
1. Run SAM-family promptable segmentation (FastSAM/MobileSAM for speed, SAM2 in Label Studio for quality) to cut out leaves and lesion areas for assisted labelling.
2. Train a small YOLOv8n-seg / YOLO-seg lesion model.
3. Compute percent of leaf area affected and map it onto the Stover scale modified by Gauhl (grades 0 to 6) and a disease severity index.
4. Overlay an EigenCAM/Grad-CAM heatmap so farmers see where the model looked.

A 2025 peer-reviewed YOLOv8m-seg study on UAV images of Black Sigatoka and Moko shows this is feasible (mAP50 84.9%).

### Cited Findings
- **Oviedo et al. 2025 (Technologies 13(9):382).** A customised YOLOv8m-seg segments and classifies Moko and Black Sigatoka lesions in UAV imagery of banana crops: precision 79.6%, recall 80.3%, mAP@0.5 84.9%, mAP@0.5:0.95 62.9%. Self-reported in the preprint. The authors note most prior work did "general leaf classification or severity scoring without precise leaf-level segmentation". — [MDPI Technologies](https://www.mdpi.com/2227-7080/13/9/382); [Preprints.org](https://www.preprints.org/manuscript/202507.1095/v1)
- **UAV banana disease detection, Selvaraj et al., ISPRS J. 2020.** RetinaNet + custom classifier on UAV-RGB reached 99.4% (banana bunchy top), 92.8% (Xanthomonas wilt), 93.3% (healthy clusters) and 90.8% (individual healthy plants). Pixel-based random forest on multispectral satellite images reached 97% OA, Kappa 0.96. Not Sigatoka. — [CORE PDF](https://core.ac.uk/download/387252778.pdf); [CGSpace record](https://cgspace.cgiar.org/items/1e1b2c92-003a-4d86-9779-11785a8f85fe)
- **Follow-up (Mora, Selvaraj et al. 2024).** RGB and panchromatic UAV images performed very well with Faster R-CNN and YOLOv8, while multispectral suffered from lower spatial resolution. Supports keeping the RGB ZED X Mini. — [Univ. Augsburg OPUS](https://opus.bibliothek.uni-augsburg.de/opus4/frontdoor/index/index/docId/121918)
- **Tumaini, Selvaraj et al., Plant Methods 2019.**
  - ResNet50, InceptionV2 and MobileNetV1 were trained by transfer learning; ResNet50/InceptionV2 beat MobileNetV1, and most models were above 90%.
  - The underlying database held about 20,000 field images from Africa, Latin America and South India, with 90% detection success in multi-country testing.
  - Black Sigatoka is among the six targets. The app was in beta in 2019; current status unknown.
  - Sources: [Plant Methods DOI](https://doi.org/10.1186%2Fs13007-019-0475-z); [Alliance Bioversity–CIAT](https://alliancebioversityciat.org/es/node/18016); [PlantwisePlus blog](https://blog.plantwise.org/2019/09/02/a-new-ai-powered-app-scans-banana-crops-for-early-signs-of-disease/)
- **Earlier severity app.** A 2020 Colombian mobile app for Black Sigatoka graded severity with a pixel-level (non-deep-learning) algorithm. — [Visión Electrónica, U. Distrital](https://geox.udistrital.edu.co/index.php/visele/article/download/15906/17483/106661)
- **Stover scale modified by Gauhl, grades 0 to 6.**

  | Grade | Leaf area affected |
  |---|---|
  | 0 | No symptoms |
  | 1 | 1% |
  | 2 | 2 to 5% |
  | 3 | 5 to 15% |
  | 4 | 16 to 33% |
  | 5 | 34 to 50% |
  | 6 | >50% |

  Source: [USDA GRIN method 495379](https://npgstest.ars-grin.gov/gringlobal/method?id=495379)
- **Disease severity index.** DSI = [Σ(n·b) / ((N−1)·T)] × 100, where n = leaves per grade, b = grade, N = number of grades, T = total leaves. Single source; the ×100 is inferred. — [CIAT study via CORE](https://core.ac.uk/download/132678283.pdf)
- **R implementation.** `ecotoxicology::ScaleGauhlStover` implements the scale. — [rdocumentation](https://www.rdocumentation.org/packages/ecotoxicology/versions/1.0.1/topics/ScaleGauhlStover)
- **Segment-anything speeds (Ultralytics docs, CPU).**

  | Model | CPU latency |
  |---|---|
  | SAM-b | 41,703 ms/im |
  | SAM2-b | 28,867 ms/im |
  | SAM2-t | 23,430 ms/im |
  | MobileSAM | 23,802 ms/im |
  | FastSAM-s | 58.0 ms/im |

  MobileSAM is about 12 ms/im on GPU (8 ms encoder + 4 ms decoder) vs about 456 ms for the original SAM. Figures vary between doc versions. — [Ultralytics FastSAM](https://docs.ultralytics.com/models/fast-sam); [Ultralytics MobileSAM](https://docs.ultralytics.com/models/mobile-sam)
- **Label Studio + SAM2.** Separate image and video ML backends exist for SAM2. Interactive mode takes keypoint/rectangle prompts and returns brush masks; SAM2 was GPU-only as of Aug 2024. The SAM1 backend has a MobileSAM Docker Compose quickstart. — [Label Studio SAM2 blog](https://labelstud.io/blog/segment-anything-2); [SAM2 image tutorial](https://labelstud.io/tutorials/segment_anything_2_image); [SAM (MobileSAM) tutorial](https://docs.humansignal.com/tutorials/segment_anything_model)
- **Explainability.** YOLOv8 lacks built-in Grad-CAM-style XAI. `pytorch-grad-cam` (jacobgil) provides EigenCAM (PCA of activations, no target needed) and Grad-CAM with `ClassifierOutputTarget`. `YOLOv8-Explainer` (PyPI) wraps EigenCAM/EigenGradCAM for detection. — [pytorch-gradcam-book](https://jacobgil.github.io/pytorch-gradcam-book/introduction.html); [EigenCAM for YOLOv5](https://jacobgil.github.io/pytorch-gradcam-book/EigenCAM%20for%20YOLO5.html); [YOLOv8-Explainer](https://github.com/Spritan/YOLOv8_Explainer); [Datature EigenCAM for YOLOv8](https://www.datature.io/blog/understanding-your-yolov8-model-with-eigen-cam)

### Inferences
- **Two-stage severity pipeline.** Effort 1 to 3 weeks, $0, very high expo value.
  - (a) Leaf mask: FastSAM-s, or a YOLOv8n-seg "leaf" class trained from SAM-assisted masks.
  - (b) Lesion mask: YOLOv8n-seg with classes "lesion_early (streak/spot)" and "necrosis", trained on 150 to 300 SAM2-assisted masked images.
  - (c) %area = lesion pixels / leaf pixels, mapped to Stover-Gauhl grade 0 to 6.
  - (d) Per-plant or per-zone DSI.
  - Report "grado estimado" as an assistive estimate with an agronomist-confirm button, not as a diagnosis.
- **Mixed geometry.** From drone altitude, single leaves and the Stover leaf-position protocol (youngest leaf with spots, leaves 3 to 5) are hard to observe. Use the drone for zone-level incidence and canopy necrosis screening, and phone close-ups for leaf-level Stover grading (inference based on field protocol below and the Q6 preaviso sources).
- **Grad-CAM on the existing classifier.** Effort about 1 day. Wrap the Ultralytics classification `nn.Module` so `forward` returns logits, target the last C2f/Conv block, and render a semi-transparent heatmap in the review queue and the farmer view. Caveat to show at the expo: heatmaps are coarse, and they can reveal shortcut learning (e.g., the model looking at soil or sky). That makes them a useful debugging tool for the team too.
- **Jetson runtime.** With TensorRT FP16 headroom (Q2), a YOLOv8n-seg at 384 to 640 px should run on the Jetson in real time. FastSAM-s is fast enough for on-demand leaf masks on the laptop CPU (about 58 ms on an M4 Pro; probably slower on a budget laptop). Use full SAM/SAM2 only offline for labelling.

### Gaps
- I did not find a published deep-learning model that directly regresses the Stover-Gauhl grade for Black Sigatoka from images.
- The Oviedo et al. paper's per-class metrics were not retrieved.
- No SAM2 Jetson Orin Nano latency figures were found.

## 5. Low-cost data collection and labelling (Label Studio/CVAT, smartphone protocols, citizen and extension-worker labelling, inter-annotator agreement)

### Takeaway
Use free, self-hostable Label Studio with the SAM/MobileSAM ML backend for masks, and keep classification triage in the team's own Flask review queue. Write a one-page capture protocol based on standard leaf positions (leaves 3, 4, 5 of young plants, as used in the Sigatoka "preaviso biológico"). Train labellers with standard area diagrams (SADs). Measure agreement, with Cohen's/Fleiss' kappa for classes and ICC for % severity, before trusting crowd labels. Published SAD studies show reliability rising to an ICC of 0.95 with SADs plus training.

### Cited Findings
- **Training and SADs, peanut late leaf spot (2025).** Combining online training sessions with SADs gave inter-rater ICC 0.95, vs 0.93 for SADs alone and 0.84 for training alone. — [INTA repository](https://repositorio.inta.gob.ar/handle/20.500.12123/21707)
- **Onion botrytis leaf blight.** With 16 untrained raters on 50 leaves, SADs significantly cut absolute error and raised mean pairwise R² from 0.681 to 0.796. — [EPAGRI Escala Botrytis 2018](https://ciram.epagri.sc.gov.br/ciram_arquivos/cebola/acervo/Escala%20Botrytis_2018.pdf)
- **Gerbera gray mold and potato common scab.** SADs improved inter-rater reliability at two labs, with the largest gains for the least accurate raters. A six-level SAD improved accuracy and reduced bias. — [INTA/argentina.gob.ar SAD potato scab](https://www.argentina.gob.ar/inta/ciap/standard-area-diagram-potato-common-scab-comparable-performance-image-and-object-based)
- **Wheat Septoria.** Agreement was high over 0 to 100% severity but weak within narrow 10% bands, so reliability must be reported per severity range. — [APS 2014 abstracts](https://www.apsnet.org/meetings/annual/meetingarchives/2014annual/Pages/2014abstracts.aspx?LID=72)
- **Field protocol (preaviso biológico for Sigatoka).** Weekly monitoring of 30 young plants in groups of 10. Infection stage is recorded on leaves 3, 4 and 5. Variables include leaf emission rate, "suma bruta" (infected leaves × severity coefficient) and "estado evolutivo". — [ESPOL thesis ch.2](https://dspace.espol.edu.ec/bitstream/123456789/14729/6/CAPITULO%202.pdf); [Agroecosistemas 2021](https://doaj.org/article/c6f906b6a4f34318b1d9c3cff90db2ae)
- **Label Studio SAM tooling.** SAM2 interactive image backend (point/box prompts to brush masks) and a MobileSAM-based SAM1 backend via Docker Compose. — [Label Studio SAM2 tutorial](https://labelstud.io/tutorials/segment_anything_2_image); [Label Studio SAM tutorial](https://docs.humansignal.com/tutorials/segment_anything_model)
- **Scale of an existing community dataset.** Tumaini's database: about 20,000 pre-screened field images from Africa, Latin America and South India. — [Alliance Bioversity–CIAT](https://alliancebioversityciat.org/es/node/18016)

### Inferences
- **Capture protocol card** (Spanish, pictograms, 1 page). Effort 1 day, $0.
  - (1) Photograph leaf 3, 4 or 5 of a plant without a bunch, upper side, filling about 70% of the frame.
  - (2) Take one shot in shade and avoid direct backlight.
  - (3) Keep it 30 to 50 cm away, with no fingers covering lesions.
  - (4) Take 1 close-up + 1 whole-plant shot.
  - (5) Make sure EXIF GPS is on, or let the app tag GPS.
  - (6) Have the farmer or extension worker tap their own guess ("sana / sigatoka / no sé").
  - Have the PWA enforce blur and brightness checks (Laplacian variance, mean luminance) before accepting a photo.
- **Labelling workflow.**
  - (a) Model pre-labels.
  - (b) The extension worker confirms or corrects in the PWA (3 big buttons).
  - (c) Images with disagreement or low calibrated confidence go to an agronomist.
  - (d) A random 10% "gold" subset is double-labelled.
  - Compute Cohen's kappa (2 raters) or Fleiss' kappa (many raters) for class labels (sklearn `cohen_kappa_score`, statsmodels `fleiss_kappa`), and ICC (pingouin `intraclass_corr`) for % severity.
  - Show the kappa/ICC on a dashboard per labeller. Use Dawid-Skene or simple majority-weighted-by-accuracy to merge crowd labels.
- **Standard area diagram.** Build one for Black Sigatoka from the team's own SAM-segmented images at the Stover-Gauhl grade breakpoints (1%, 5%, 15%, 33%, 50%). Use it as the on-screen reference when labellers grade severity. This replicates the documented reliability gains at zero cost.
- **CVAT** (open-source, also supports SAM-assisted annotation) is an alternative. Label Studio's ML-backend pattern fits the existing Python stack and the team's own model as a pre-annotator.

### Gaps
- No search results covered CVAT's SAM integration, so CVAT capabilities are not verified here.
- I found no published inter-annotator agreement study specific to Black Sigatoka image grading.
- No source gave a validated smartphone capture protocol for Sigatoka imaging. The protocol above is an inference from field-monitoring practice.

## 6. Turning detections into decisions (incidence maps, weather-based risk, offline reports, WhatsApp/SMS, Spanish/indigenous-language voice UI, low-literacy design)

### Takeaway
Aggregate geotagged predictions into H3 hexagons (res 11 ≈ 0.2 ha, res 10 ≈ 1.5 ha, res 9 ≈ 10.5 ha) to give per-zone incidence and severity maps on the existing Leaflet map. Combine them with a free, key-less weather risk layer: Open-Meteo forecast with 16 days ahead and 92 past days, plus NASA POWER hourly history since 2001. Use simple published Sigatoka thresholds: optimum about 27 °C, germination drops below 20 °C, RH ≥ 90 to 92% or leaf wetness, and infection completes in about 12 h of wetness at 27 °C. Output a one-page Spanish PDF/image report that can be shared to WhatsApp with the Web Share API (HTTPS required). Read results aloud with offline TTS.

### Cited Findings
- **H3 average cell areas and edge lengths.**

  | Res | Avg area | Avg edge length |
  |---|---|---|
  | 8 | 0.737 km² | 531 m |
  | 9 | 105,333 m² | 201 m |
  | 10 | 15,048 m² | 75.9 m |
  | 11 | 2,150 m² | 28.7 m |
  | 12 | 307 m² | 10.8 m |

  Areas use a spherical WGS84 authalic-radius model. — [H3 resolution table](https://h3geo.org/docs/core-library/restable/)
- **Open-Meteo hourly variables.**
  - `relative_humidity_2m`, `dew_point_2m`, `precipitation` (preceding-hour sum), `vapour_pressure_deficit` (kPa), soil moisture at 5 depths, and `et0_fao_evapotranspiration`.
  - A daily "Mean Leaf Wetness Probability" is listed without a definition.
  - `forecast_days` 0 to 16 and `past_days` 0 to 92.
  - An API key is "only required to commercial use", and a self-hosted licence option exists.
  - Source: [Open-Meteo docs](https://open-meteo.com/en/docs)
- **Open-Meteo `leaf_wetness_probability`.** Listed as an agricultural hourly variable in an Open-Meteo OpenAPI spec (third-party mirror). — [open-meteo MCP openapi.yml](https://glama.ai/mcp/servers/@cmer81/open-meteo-mcp/blob/02fbd67dd8f200dc1ecb9ac51aad33d7d81c2483/openapi.yml)
- **NASA POWER.** No API key required. Agroclimatology community "AG" variables include T2M, RH2M and PRECTOTCORR. The hourly API is limited to 15 parameters per query, and hourly data run from 2001-01-01 to near-real-time. Precipitation units differ by temporal API, so verify them. — [nasapower R client docs](https://docs.ropensci.org/nasapower/reference/get_power.html); [GeoDataAccess.jl NASA POWER](https://rallypointone.github.io/GeoDataAccess.jl/dev/sources/nasa_power.html)
- **Climate drivers of Sigatoka.**
  - Ascospores germinate between 10 and 38 °C, optimum about 27 °C, with a strong decline below 20 °C.
  - Conidia germinate at RH 92 to 100%; ascospores need 98 to 100%.
  - Conidia form under high humidity, especially with a water film on the leaf.
  - A Costa Rican study found favourable conditions at mean T > 23 °C and mean RH > 75%.
  - Sources: [Atena Editora (Teapa, Tabasco)](https://atenaeditora.com.br/catalogo/post/condiciones-climaticas-que-favorecen-la-infestacion-de-sigatoka-negra-mycosphaerella-fijiensis-morelet-amorfo-pseudocercospora-fijiensis-morelet-deighton-en-el-area-bananera-de-teapa-tabasco-mexico); [ESPOL Revista Tecnológica](https://rte.espol.edu.ec/index.php/tecnologica/article/download/65/36/104); [TEC Costa Rica AgroInnovación](https://revistas.tec.ac.cr/index.php/agroinn/article/download/6503/6351)
- **Teapa, Tabasco (59 years of climate data).** October to March (autumn-winter) is the most favourable period; spring-summer is least favourable. RH was estimated from daily minimum and mean temperature. — [Atena Editora](https://atenaeditora.com.br/catalogo/post/condiciones-climaticas-que-favorecen-la-infestacion-de-sigatoka-negra-mycosphaerella-fijiensis-morelet-amorfo-pseudocercospora-fijiensis-morelet-deighton-en-el-area-bananera-de-teapa-tabasco-mexico); [Revista Agroproductividad](https://revista-agroproductividad.org/index.php/agroproductividad/en/article/view/2500)
- **Published risk-model logic.**
  - Orlandini's model (Univ. of Florence) uses hourly T, RH and rain, with RH > 85% as a leaf-wetness proxy where leaf-wetness duration (LWD) is unavailable. — [Orlandini model illustration, CIMH](https://cami.cimh.edu.bb/files/PUBCOMM/PresK11/PDF/orlandini_%20Diseases_%20Model_Illustration_Black_Sigatoka.pdf)
  - The Pessl FieldClimate infection model treats infection as complete at 27 °C within 12 h of leaf wetness or RH ≥ 91%. — [ABIM 2011, Denzer](https://www.abim.ch/fileadmin/abim/documents/presentations2011/Session6/3_Heiner_Denzer_ABIM2011.pdf)
  - The CATIE bioclimatic system (Jiménez Otárola et al., 1993) links accumulated rain duration to leaf-4 infection, has two-week predictive character, and was field-tested in Turrialba. — [CATIE/Kimuk record](https://kimuk.conare.ac.cr/Record/RCATIE_4730b835453d98994bba753cc33d65e3?lng=fr)
  - A CATIE biometeorological pre-warning system (1995) combines climate data with the biological pre-warning. — [Kimuk record](https://kimuk.conare.ac.cr/Record/RCATIE_026452dd4013d0d4c419821a1411271c?lng=de)
  - Benavides López et al. (2018, Río Frío) found precipitation duration, mean T, RH, leaf humidity and solar radiation were the strongest predictors of pathogen DNA on leaf 1. — [TEC AgroInnovación issue](https://revistas.tec.ac.cr/index.php/agroinn/issue/download/646/160)
- **Banalytic (Ghana/Brazil, UK-funded).** An early-warning project using Neural ODEs on sensor and satellite data to send location-specific infection-risk alerts via a mobile app; in development. — [IUK Business Connect](https://iuk-business-connect.org.uk/projects/climate-smart-agriculture/banalytic/)
- **Web Share API.**
  - Call `navigator.canShare({files})` and then `navigator.share({files, title, text})`.
  - PDFs (`application/pdf`) are usually shareable.
  - Requires HTTPS and user activation, and is gated by the `web-share` Permissions Policy.
  - Not Baseline across browsers.
  - Source: [MDN canShare](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/canShare); [MDN share](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share)
- **Offline voice.**
  - Vosk offers offline Android speech recognition, including Spanish, with portable models of about 50 MB per language. Informal, dated source. — [F-Droid forum](https://forum.f-droid.org/t/vosk-speech-recognition-library/9793)
  - Piper (Rhasspy) is a fast, CPU-only, offline neural TTS (MIT licence) with Spanish voices. Aggregator source. — [tts.ai Piper voices](https://tts.ai/voices/piper/?lang=gl)

### Inferences
- **Incidence map.** Effort 1 to 2 days, $0.
  - In Flask, `h3.latlng_to_cell(lat, lon, 11)` for each geotagged prediction, aggregated per cell: n_images, % sigatoka (calibrated), mean severity grade and last-visit date.
  - Render with `h3-js` + Leaflet polygons in a 3-colour traffic-light palette (verde/amarillo/rojo) with hatch patterns for colour-blind users.
  - Use res 11 for drone flights over a smallholding and res 9 for community or ejido-level summaries.
  - Grey out cells with fewer than 5 images ("sin datos suficientes") to avoid false alarms.
- **Weather risk index.** Effort 2 to 3 days, $0.
  - Cache the last Open-Meteo pull (forecast + `past_days=14`) in SQLite so the laptop works offline with the most recent forecast.
  - Each hour, flag "favourable" if T is 20 to 30 °C AND (RH ≥ 90% OR precipitation > 0 OR dew-point depression < 1 °C). Thresholds come from the sources above; RH 85 to 92% cut-offs differ between models, so make it a setting.
  - Sum favourable hours per rolling 7 days into a Bajo/Medio/Alto weekly risk.
  - Backfill climatology with NASA POWER hourly (T2M, RH2M, PRECTOTCORR) to show "this October vs the 2001 to 2025 average".
  - Label it an "índice de condiciones favorables", not a validated forecast, and validate it against the team's own detection time series.
- **Decision rule shown to farmers.** "Alto riesgo climático + ≥X% hexágonos con sigatoka → deshoje/cirugía de hojas afectadas y avisar al técnico."
  - Leaf removal and sanitation are standard low-cost cultural controls, but the exact recommendations should come from the partner agronomist or the local plant-health agency.
  - No chemical dose advice in the app.
- **Offline report.**
  - Server-side: ReportLab or WeasyPrint in Flask produces a 1-page PDF (map snapshot, counts, 3 example photos with heatmaps, risk gauge, QR code to the flight record).
  - Client-side: jsPDF or an HTML-to-PNG card, shared through `navigator.share` with a `wa.me/?text=` link fallback.
  - An image card (PNG) is more readable in WhatsApp than a PDF for low-literacy users.
  - SMS fallback: a 160-character summary ("Parcela Juan: 3/20 zonas con sigatoka, riesgo ALTO esta semana. Revise hojas 3-5.").
- **Low-literacy UI.**
  - Icon + colour + one word ("SANA" ✓ green / "SIGATOKA" ⚠ red / "NO SÉ – repetir foto" ? grey).
  - A large speaker button that plays a pre-recorded or Piper-generated Spanish audio message.
  - Pre-recorded audio clips by native speakers for indigenous languages (Tseltal, Tsotsil, Ch'ol in Chiapas; Chontal in Tabasco). This is cheaper and more trustworthy than machine TTS, which largely does not exist for these languages (inference; not verified).
  - Make language a first-run choice with flag-free icons.

### Gaps
- I could not retrieve the full Orlandini model equations (the PDF fetch failed) or the exact "suma de evolución" formula. The thresholds above are a simplified, unvalidated composite.
- Open-Meteo's definition and model coverage for `leaf_wetness_probability`, and its non-commercial rate limits, were not confirmed on the official page.
- No source was found on WhatsApp's behaviour as a Web Share target from a PWA on Android/iOS; test on target phones.
- No offline ASR/TTS models were found for Mexican indigenous languages (Tseltal, Tsotsil, Ch'ol, Chontal); not researched in depth.
- No SENASICA (Mexico) Sigatoka technical sheet was retrieved.

## 7. Lightweight remote agronomist involvement and privacy / data-ownership practices

### Takeaway
Make the existing human-review queue asynchronous and exportable. A field laptop or phone accumulates "uncertain" cases offline, then syncs a small bundle (thumbnails + predictions + GPS rounded to an H3 cell) when connectivity appears. An agronomist reviews it on any browser and the labels flow back into retraining. Pair this with community data governance under the CARE principles and Mexico's new personal-data law (LFPDPPP, in force 21 March 2025): consent, location blurring, local-first storage and community ownership.

### Cited Findings
- **CARE Principles for Indigenous Data Governance** (Collective benefit, Authority to control, Responsibility, Ethics). Developed by the Global Indigenous Data Alliance in 2019 to complement FAIR. They stress that data ecosystems should let Indigenous Peoples derive benefit and that their rights and interests in data must be recognised. — [Wikipedia: CARE Principles](https://en.wikipedia.org/wiki/CARE_Principles_for_Indigenous_Data_Governance); [Ada Lovelace Institute](https://www.adalovelaceinstitute.org/?p=3573); [ARDC](https://ardc.edu.au/?p=12938)
- **Mexico's new LFPDPPP.** Published in the DOF 20 March 2025 and in force 21 March 2025, replacing the 2010 law. INAI's private-sector data-protection functions moved to the Secretaría de Anticorrupción y Buen Gobierno, and challenges now go by amparo. Commentators cite new or strengthened obligations on privacy notices, consent, sensitive data and higher sanctions. — [Garrigues](https://www.garrigues.com/es_ES/noticia/mexico-nueva-ley-federal-proteccion-datos-personales-posesion-particulares-introduce); [Littler](https://www.littler.com/es/news-analysis/asap/mexico-tiene-nueva-ley-en-materia-de-proteccion-de-datos-personales); [IDC Online](https://idconline.mx/corporativo/2025/03/28/lfpdppp-5-cambios-clave-en-el-manejo-de-datos-personales)
- **Tumaini's network role.** It uploads data to a global system for large-scale monitoring, which illustrates the value and the governance question of pooled data. — [PlantwisePlus blog](https://blog.plantwise.org/2019/09/02/a-new-ai-powered-app-scans-banana-crops-for-early-signs-of-disease/)
- **Unknown-condition flagging.** Detecting unknown diseases is a prerequisite for continual learning. This is the technical basis for routing "unknown" cases to experts rather than auto-labelling them. — [Jiang et al. 2022](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9520169/)

### Inferences
- **Asynchronous agronomist loop.** Effort 3 to 5 days, $0.
  - (1) Export the review queue as a zip: JPEG thumbnails ≤ 200 KB, a CSV/JSON of model version, calibrated probabilities, OOD score, H3 cell and timestamp.
  - (2) Share it by USB, WhatsApp document or a free static host.
  - (3) The agronomist opens the same Flask review page in "remote mode" (or a static HTML+JS reviewer that runs from the zip) and labels with keyboard shortcuts.
  - (4) The labels file is imported back, deduplicated, recorded with reviewer ID, and counted toward inter-annotator agreement (Q5).
  - Prioritise by calibrated uncertainty × risk (high-risk weather cells first), and cap each batch at about 50 images, roughly a 10-minute review.
  - Optional: Label Studio (self-hosted) as the expert interface, with the team's model as the ML backend.
- **"Segunda opinión" button.** The farmer-facing app queues a case for the agronomist and shows status ("en revisión / revisado por Ing. X"). This builds trust and is a good expo story.
- **Privacy and data ownership**, all at $0:
  - (a) Local-first: data stays on the community's laptop by default.
  - (b) Explicit, audio-read consent in Spanish or the local language, with a printed "aviso de privacidad simplificado" aligned to the LFPDPPP.
  - (c) Strip EXIF (names, device serials) on export and coarsen GPS to H3 res 9 or 10 in anything shared outside the community; keep full-resolution GPS only locally for flight planning.
  - (d) No faces or people: OOD gate plus an optional face-blur pass before export.
  - (e) A data-sharing agreement stating the community or cooperative owns the images and labels, and the university gets a licence for research/model training. Give the community the trained model weights and the right to withdraw data (CARE "Authority to control" and "Collective benefit").
  - (f) Record a datasheet / model card per version: data sources, regions, known failure modes, field-exam accuracy.
- **Model versioning.** Already present. Tie every prediction to `model_version` and `T` (temperature) so agronomist corrections can be traced to the model that produced them.

### Gaps
- I did not find agriculture-specific data-governance codes from Mexico, or examples of Sigatoka programs with community data agreements.
- The status of the LFPDPPP's implementing regulations (a 90-day deadline after March 2025) was not confirmed.
- No published evaluation of asynchronous agronomist review for plant-disease apps was found in the time available.
