# State of the art (2019–2026): AI / computer-vision detection of Black Sigatoka, Yellow Sigatoka and other banana leaf diseases from leaf/phone and drone (UAV) RGB images

Research notes compiled 8 Nov 2026. Bibliographic metadata (authors, venue, volume, DOI) for every DOI below was checked against the Crossref, OpenAlex or Europe PMC APIs in this session; all of them returned a matching record. Numbers are copied as the abstracts or full texts state them. "Preprint" and "conference" are flagged. Where a number comes only from a search-engine snippet and not from the primary text, it is marked **[snippet-only]**.

Project context used for relevance: YOLOv8n-cls, 3 classes (healthy / Sigatoka / other), 384×384 input, 91.8% top-1 on a public close-up dataset of 11,228 images. The project's own log (`vision/train/experiments.md`) gives the per-class counts as sana 3,029 / sigatoka 3,226 / otra 4,973.

---

## Q1. Peer-reviewed deep-learning studies on Sigatoka and other banana diseases: models, data, image source, accuracy, field validation

### Takeaway
Close-up phone images: most published classifiers report 87–99% accuracy, but they are scored on held-out images from the same dataset. Drone/UAV work scores much lower and is evaluated per object: about 55–86% mAP@50 or precision/recall (YOLOv9 aerial), 84.9% mAP@0.5 (YOLOv8-seg, Ecuador) and 86.5% (MobileNetV2 on multispectral false colour). Almost no Sigatoka study tests on independent field data from a different farm, region or season. The strongest system-level reference is CIAT/Bioversity's Tumaini work. It reports per-region, per-plant-part results, and its Black Sigatoka leaf mAP@0.5 ranges from 0.80 to 0.90.

### Cited Findings

**Leaf / phone / ground-level images**
- **Selvaraj et al. 2019, Plant Methods 15:92** (CIAT/Bioversity; the paper behind the Tumaini app). Retrained three CNN architectures with transfer learning and built 6 models covering 18 classes ("disease by plant parts"). Images were "expert pre-screened" and collected "from various hotspots in Africa and Southern India". ResNet50 and InceptionV2 models beat MobileNetV1, with "an accuracy of more than 90% in most of the models tested". SSD MobileNetV1 was evaluated for future phone use. — [Selvaraj et al. 2019, doi:10.1186/s13007-019-0475-z](https://doi.org/10.1186/s13007-019-0475-z)
  - The dataset is about 18,000 field images, per the FAO e-Agriculture summary of the paper. Press coverage says "20,000 images" and an "average 90 percent" detection rate across Colombia, DR Congo, India, Benin, China and Uganda. — [FAO e-Agriculture](https://www.fao.org/e-agriculture/news/article-ai-powered-banana-diseases-and-pest-detection); [Alliance Bioversity–CIAT news](https://alliancebioversityciat.org/es/node/18016)
- **Mora et al. 2025, Scientific Reports 15:3491** (CIAT/Bioversity). "Digital framework for georeferenced multiplatform surveillance of banana wilt using human in the loop AI and YOLO foundation models".
  - Data: ground-level images from the CGIAR banana image library, with 70,263 annotations. The RGB UAV dataset has ~23,584 annotations. Drones: DJI Phantom 4 Pro (FC6310) and Mavic 2 Pro (Hasselblad L1D-20c), flown at 60 m, giving GSD of 1.36 and 1.21 cm.
  - Models: YOLO-NAS, YOLOv8, YOLOv9 and Faster R-CNN were compared. YOLOv9 was best on aerial images (healthy / Fusarium wilt / Xanthomonas wilt), with "mAP@50, precision and recall … ranging from 55 to 86%". YOLOv8 was best on ground images, at "65 and 99% depending on the plant part and region".
  - Leaf-level mAP@0.5 is the weakest plant part. Black Sigatoka on leaves scored 0.80 (Africa), 0.90 (Latin America), 0.90 (Asia) and 0.86 (Australia). "Black Sigatoka + Yellow Sigatoka" on leaves scored 0.81 (India). Healthy-leaf mAP was only 0.60–0.71 across regions.
  - Uses Grad-CAM and Human-in-the-Loop AI. The Tumaini app is linked to an online PostgreSQL disease map. The map holds 70,953 plants, including 351 Black Sigatoka and 1,999 "Black Sigatoka + Yellow Sigatoka" plants. Licence: CC BY-NC-ND 4.0. — [Mora et al. 2025, doi:10.1038/s41598-025-87588-2](https://doi.org/10.1038/s41598-025-87588-2) (full text via [PMC11775237](https://pmc.ncbi.nlm.nih.gov/articles/PMC11775237/))
- **Sanga, Machuve & Jomanga 2020, Eng. Technol. Appl. Sci. Res. 10(3):5674–5677** (Tanzania). Compared VGG16, ResNet18, ResNet50, ResNet152 and InceptionV3, with accuracies from "95.41% for InceptionV3 to 99.2% for Resnet152". InceptionV3 was chosen for the phone because it "demands much less memory". The paper reports 99% confidence on leaves "captured … from the real environment". That is a confidence figure, not a measured field accuracy. — [doi:10.48084/etasr.3452](https://doi.org/10.48084/etasr.3452)
- **Elinisa & Mduma 2024, Smart Agricultural Technology 7:100423** (Tanzania). A CNN trained on 27,360 images of diseased and healthy banana leaves and stalks reached 91.17% accuracy. It was deployed in a mobile app that classifies in under 5 s per image. — [doi:10.1016/j.atech.2024.100423](https://doi.org/10.1016/j.atech.2024.100423); numbers from [DOAJ record](https://doaj.org/article/ed658bfba39341b98a3dadd7916babdd) **[snippet-only]**
- **Elinisa, Maina, Vodacek & Mduma 2024, Applied Artificial Intelligence 39(1):2440837.** U-Net semantic segmentation of Fusarium wilt and Black Sigatoka, trained on 18,240 leaf and stalk images taken with phones on farms. Dice 96.45%, IoU 93.23%. — [doi:10.1080/08839514.2024.2440837](https://doi.org/10.1080/08839514.2024.2440837) (abstract via Semantic Scholar API)
- **Kambo, Nyambo, Leo & Ally 2024, Indian J. Sci. Technol. 17(37):3889–3897** (NM-AIST, Tanzania). Classifies Black Sigatoka infection stages. A basic CNN reached 96% training and 89% validation accuracy, with precision, recall and F1 averaging 0.90. VGG16 reached 92%/89%, with precision 0.80, recall 0.75 and F1 0.75. This is a low-tier journal. — [doi:10.17485/ijst/v17i37.2453](https://doi.org/10.17485/ijst/v17i37.2453)
  - The four stages (healthy, early, intermediate, advanced) are named in the NM-AIST repository record. — [NM-AIST DSpace](https://dspace.nm-aist.ac.tz/items/bd39b826-35b0-4052-98dc-42e3625d11ff)
- **Bhuiyan et al. 2023, Smart Agricultural Technology 4:100214.** BananaSqueezeNet, a lightweight CNN with Bayesian optimisation, trained on Bangladesh images (leaf blight, Sigatoka, Cordana). Accuracy 0.9625, precision 0.9653, recall 0.9625, specificity 0.9875, F1 0.9617, MCC 0.9513. It beats EfficientNetB0, MobileNetV3 and ResNet-101. — [doi:10.1016/j.atech.2023.100214](https://doi.org/10.1016/j.atech.2023.100214)
- **Jiménez et al. 2025, AI (MDPI) 6(3):61** (Ecuador). 900 leaf images (300 Black Sigatoka, 300 Cordana, 300 healthy), augmented to 9,000. Accuracy: EfficientNetB0 88.33%, ResNet50 88.90%, VGG19 87.22%. Augmentation "did not significantly improve" accuracy (EfficientNetB0 went to 87.83%). — [doi:10.3390/ai6030061](https://doi.org/10.3390/ai6030061)
- **Quijije et al. 2026, Frontiers in Artificial Intelligence 9** (ESPOL, Ecuador). Radiomics plus explainable ML on 14,763 public RGB leaf images: Healthy 4,866, Sigatoka 5,767, Fusarium race 1 4,130, drawn from the Tanzanian and BananaLSD data.
  - Calibrated Random Forest: accuracy 0.85, macro-F1 0.84. Fusarium recall was 0.70.
  - CNN baselines at 224 px: MobileNetV3 0.96 accuracy / 0.95 macro-F1, EfficientNet 0.96 / 0.97, ResNet-18 0.96 / 0.96.
  - The authors state there was no independent validation. They call the work "a methodological proof-of-concept rather than evidence of direct operational validity in Ecuadorian plantations" and note that CNNs "may be exploiting dataset-specific cues or backgrounds". — [doi:10.3389/frai.2026.1861135](https://doi.org/10.3389/frai.2026.1861135)
- **Nassor, Mushthofa & Priandana 2024, IOP Conf. Ser. Earth Environ. Sci. 1359:012010** (conference). Classes: black Sigatoka, Fusarium wilt race 1, healthy. Results:
  - SqueezeNet: accuracy 97.12%, precision 97.14%, recall 97.1%, F1 97.12%.
  - MobileNetV2: the smallest model, at 2.51 MB.
  - MobileNetV3-small: the largest model, at 14 MB. — [doi:10.1088/1755-1315/1359/1/012010](https://doi.org/10.1088/1755-1315/1359/1/012010)
- **Du et al. 2026, Scientific Reports.** Hybrid of MobileNetV2 and ResNet101 with attention and PCA feature fusion, run on 3 public datasets (Banana and Banana Leaf, Banana Disease Recognition, BananaLSD). Accuracy 98.28, precision 98.18, recall 98.77, F1 98.43, with 12.7 M trainable parameters. — [doi:10.1038/s41598-026-47092-7](https://doi.org/10.1038/s41598-026-47092-7)
- **Escudero, Calvo & Bejarano 2021, Int. J. Machine Learning and Computing 11(4):323–326** (Univ. Tecnológica de Pereira, Colombia). A LeNet CNN detects infection progress in leaf regions, and a decision tree then classifies "level of infection severity". The method is reported as robust to photometric variation. — [doi:10.18178/ijmlc.2021.11.4.1055](https://doi.org/10.18178/ijmlc.2021.11.4.1055)
- **Singh, Kumar, Shobhit & Chandel 2024, IEEE IATMSI** (conference). ResNeXt50 graded Sigatoka "seriousness" on 10,000 leaf photos with 5 levels, reaching 95.53% overall accuracy **[snippet-only]**. — [doi:10.1109/iatmsi60426.2024.10503074](https://doi.org/10.1109/iatmsi60426.2024.10503074); [IEEE Xplore](https://ieeexplore.ieee.org/document/10503074/)
- **Preprints, not peer-reviewed:**
  - KHO-YOLOv8 (Research Square 2025): more than 5,000 samples in 3 classes (healthy, Xanthomonas wilt, Sigatoka), 96.47% accuracy. — [doi:10.21203/rs.3.rs-6812770/v1](https://doi.org/10.21203/rs.3.rs-6812770/v1)
  - BananaVLM (arXiv, 27 Aug 2026): LLaVA-v1.5-7B fine-tuned with LoRA on ~80,000 auto-generated Q&A pairs. 92.21% in-domain and 83.28% out-of-domain accuracy on a 9-class benchmark, and 98.38% binary healthy/diseased out-of-domain accuracy. Reported margin over Gemini 2.5 Pro: +49.8 points in-domain and +63.3 points out-of-domain. — [arXiv:2609.25040](https://arxiv.org/abs/2609.25040)

**UAV / aerial images**
- **Gómez Selvaraj et al. 2020, ISPRS J. Photogramm. Remote Sens. 169:110–124** (DR Congo, Benin). UAV RGB "mixed model": a RetinaNet detector plus a custom classifier. Per-class accuracy: banana bunchy top 99.4%, Xanthomonas wilt 92.8%, healthy clusters 93.3%, healthy individual plants 90.8%. A pixel-level Random Forest on satellite/MicaSense data reached up to 97% overall accuracy (Kappa 0.96). Sigatoka is not a target class. — [doi:10.1016/j.isprsjprs.2020.08.025](https://doi.org/10.1016/j.isprsjprs.2020.08.025)
- **Calou et al. 2020, Biosystems Engineering 193:115–125** (Ceará, Brazil; Yellow Sigatoka). Monthly UAV flights with a 16-MP RGB camera (an Inspire 1, per the dissertation). Five classifiers were compared against field assessment. Best result for September 2017: 99.28% overall accuracy, Kappa 97.13.
  - **Conflict:** the abstract as quoted names SVM as the best classifier, while the author's 2018 dissertation abstract names Minimum Distance. — [doi:10.1016/j.biosystemseng.2020.02.016](https://doi.org/10.1016/j.biosystemseng.2020.02.016); [UFC dissertation](https://repositorio.ufc.br/ri/handle/riufc/41608)
- **Linero-Ramos et al. 2024, Drones 8(9):503** (Magdalena, Colombia). 505 original drone images were tiled into 2,706 diseased-leaf, 3,102 healthy-leaf and 1,192 non-leaf objects, plus 3,640 Black Sigatoka labels from phytopathologists. MobileNetV2 on false colour (red, red-edge, NIR) reached 86.5% for 3 classes. — [doi:10.3390/drones8090503](https://doi.org/10.3390/drones8090503)
- **Oviedo et al. 2025, Technologies (MDPI) 13(9):382** (Ecuador, Cavendish). YOLOv8 instance segmentation of Moko and Black Sigatoka from UAV images, comparing seven configurations. Best: precision 79.6%, recall 80.3%, mAP@0.5 84.9%, mAP@0.5:0.95 62.9%. The authors note that mixed or overlapping symptoms in an occluded canopy are a failure mode. The preprint is [Preprints.org 202507.1095](https://www.preprints.org/manuscript/202507.1095/v1). — [doi:10.3390/technologies13090382](https://doi.org/10.3390/technologies13090382)
  - A companion web system, "AI-BananaMapping" (CCIS 2025, pp. 213–227), adds geolocation of detections. — [doi:10.1007/978-3-032-08366-1_14](https://doi.org/10.1007/978-3-032-08366-1_14)
- **Thai, Le & Nguyen 2025, Computers and Electronics in Agriculture 231:109927** (Vietnam). EF-CenterNet is an anchor-free detector (EfficientViT block plus FPN) for banana leaf disease in UAV images under real field conditions. It needs at least 2.09× fewer parameters and 3.18× fewer GFLOPs than the compared detectors. On a Jetson Xavier it processed at least 15% faster than competitors. The abstract gives no absolute mAP. — [doi:10.1016/j.compag.2025.109927](https://doi.org/10.1016/j.compag.2025.109927)
- **Garcia-Braham (Univ. Tecnológica de Pereira), Zenodo 2026.** "DS-v1 and DS-v2" holds UAV tiled images, partitions and YOLO-format bounding boxes for the article "UAV-based detection of Black Sigatoka in banana crops using low-cost RGB imagery and deep learning object detection". CC BY 4.0, 21.5 GB, code on GitHub. The article itself was not found; its venue and results are unknown. — [doi:10.5281/zenodo.20945958](https://zenodo.org/records/20945958)
- Mora et al. (2025) also mention "Estamos Alerta", a UAV deep-learning platform for monitoring banana disease in Ecuador. — [Mora et al. 2025](https://doi.org/10.1038/s41598-025-87588-2)

### Inferences
- The team's 91.8% top-1 on public data falls inside the 87–99% range of same-distribution leaf studies. It should be described as a within-dataset benchmark, not field performance. Most published numbers are of the same kind.
- On UAV imagery, honest per-object metrics for Black Sigatoka are around 80–90% (mAP@0.5 or precision/recall). That is well below the leaf-classifier numbers. A drone system reporting about 80% on its own independent field set would be competitive and credible.
- The closest published analogues to the team's system are:
  - Mora et al. 2025 (georeferenced map + human-in-the-loop + YOLO).
  - Oviedo et al. 2025 / AI-BananaMapping (UAV + YOLOv8-seg + web geolocation).

  The team's distinctive angle could be offline operation, onboard Jetson inference, a smallholder focus and a Mexican field validation set.

### Gaps
- The full texts of Selvaraj 2019, Linero-Ramos 2024 (the RGB vs false-colour comparison and the detection-model numbers), Oviedo 2025 (image counts, altitude, drone, dataset availability) and EF-CenterNet (absolute mAP, dataset size, Jetson FPS) could not be retrieved. The MDPI and Elsevier pages returned 403.
- No peer-reviewed deep-learning study on Black Sigatoka from Mexican plantations was found in these searches.
- Yellow Sigatoka has only Calou 2020 (classical ML on UAV RGB). It also appears as a class in some datasets (PSFD-Musa, the Mendeley sets) and as a merged "Black + Yellow Sigatoka" class in Mora 2025. No dedicated deep-learning paper was found.

---

## Q2. Public banana leaf disease datasets: size, classes, licence, image conditions, links

### Takeaway
Most public data is close-up smartphone imagery from Tanzania, Bangladesh, India and Ethiopia. Only one open dataset found targets Black Sigatoka from low-cost UAV RGB imagery: the Colombian Zenodo DS-v1/DS-v2, CC BY 4.0, YOLO boxes. No open dataset with Stover or severity labels was found. The team's 11,228-image, 3-class set matches the class structure of the Tanzanian "Banana Leaves Imagery Dataset" (healthy / Black Sigatoka / Fusarium wilt) and is close to its counts.

### Cited Findings
- **Banana Leaves Imagery Dataset (Mduma & Elinisa 2025, Scientific Data 12:477)**
  - Content: 11,767 images (3,339 healthy, 3,496 Black Sigatoka, 4,932 Fusarium wilt race 1).
  - Collection: Rungwe, Mbeya, Arumeru and Arusha districts of Tanzania, Nov 2022 – Jan 2023, on a Samsung SM-A715F at "3480 × 3496 pixels". Images were manually cropped to remove background, duplicates were removed with VisiPics and Duplicate Photo Finder, and labels were quality-checked by agricultural experts and plant pathologists.
  - Licence and location: CC BY 4.0, Zenodo [10.5281/zenodo.7670326](https://doi.org/10.5281/zenodo.7670326). No model results are given in the technical validation. — [doi:10.1038/s41597-025-04456-4](https://doi.org/10.1038/s41597-025-04456-4); [PMC11928457](https://pmc.ncbi.nlm.nih.gov/articles/PMC11928457/)
- **Mduma & Leo 2023, Data in Brief 49:109322.** 16,092 smartphone images of leaves and stems in Tanzania (Black Sigatoka, Fusarium wilt race 1, healthy), described as "the largest publicly accessible dataset for banana leaves and stems". The 2025 article says this earlier dataset sits in a Harvard repository and "did not fully represent data from all farming seasons". — [doi:10.1016/j.dib.2023.109322](https://doi.org/10.1016/j.dib.2023.109322); [PMC11928457](https://pmc.ncbi.nlm.nih.gov/articles/PMC11928457/)
- **BananaLSD (Arman et al. 2023, Data in Brief 50:109608).** 937 field images plus 1,600 augmented, in 4 classes: healthy, Sigatoka, Cordana, Pestalotiopsis. Taken with three smartphones "in diverse real-world conditions" at BSMRAU, Bangladesh, in June 2021. Mendeley [10.17632/9tb7k297ff.1](https://data.mendeley.com/datasets/9tb7k297ff/1); [Kaggle mirror](https://www.kaggle.com/datasets/shifatearman/bananalsd). — [doi:10.1016/j.dib.2023.109608](https://doi.org/10.1016/j.dib.2023.109608)
- **PSFD-Musa (Medhi & Deb 2022, Data in Brief 43:108427).** 8,000+ processed images of plant, stem, fruit and leaf from India (Malbhog, Jahaji, Kachkol, Bhimkol). Classes include Black Sigatoka, Yellow Sigatoka, Panama disease, bacterial soft rot, pests and potassium deficiency. — [doi:10.1016/j.dib.2022.108427](https://doi.org/10.1016/j.dib.2022.108427)
- **Mendeley Data sets.** Descriptions come from the search engine's summary of the Mendeley pages. Licences were not verified.
  - **Banana Leaf Disease Images** (Hailu 2021, Ethiopia): 1,288 images; healthy / Xanthomonas / Sigatoka. — [10.17632/rjykr62kdh.1](https://data.mendeley.com/datasets/rjykr62kdh/1)
  - **Banana_Leaf_Disease_Dataset_Bangladesh:** 424 images, 4 classes including Sigatoka. — [10.17632/wfzpdmc5vx.1](https://data.mendeley.com/datasets/wfzpdmc5vx/1)
  - **Banana and Banana Leaf Dataset** (Azam, Das & Kafi): 2,375 raw + 9,513 augmented images, including Black and Yellow Sigatoka. The team's notes cite V3 (2026). — [10.17632/5nfjzntwd8](https://data.mendeley.com/datasets/5nfjzntwd8/2)
  - **Banana Disease Recognition Dataset:** 7 classes including Black and Yellow Sigatoka; 2,856 augmented images. — [10.17632/79w2n6b4kf.1](https://data.mendeley.com/datasets/79w2n6b4kf/1)
- **UAV RGB, Black Sigatoka:** Garcia-Braham DS-v1/DS-v2 (2026). Tiled UAV images, partitions and YOLO-format bounding boxes; CC BY 4.0; 9.8 GB + 11.7 GB. The page does not report image counts, altitude or location. — [Zenodo 10.5281/zenodo.20945958](https://zenodo.org/records/20945958)
- **UAV multispectral, Black Sigatoka:** Linero-Ramos 2024. 505 drone images and the 2,706 / 3,102 / 1,192 objects and 3,640 expert labels described in Q1. Public availability was not confirmed. — [doi:10.3390/drones8090503](https://doi.org/10.3390/drones8090503)
- **CGIAR banana image library (CIAT/Bioversity):** 70,263 ground-level annotations and ~23,584 UAV annotations, used for Tumaini. It is described as an internal or curated library; no open download was identified. — [Mora et al. 2025](https://doi.org/10.1038/s41598-025-87588-2). The figure set for Selvaraj 2019 is on [Springer Nature figshare](https://springernature.figshare.com/collections/AI-powered_banana_diseases_and_pest_detection/4615442).
- The project's own notes also list Mendeley "BLADE: Banana Leaf Agricultural Disease Evaluation" (Mishra et al. 2026, 10.17632/w7ytz3twjv.2) and "Banana Leaf Disease Dataset of Bangladesh" (Islam et al. 2026, 10.17632/wzshm7ky49.1). Their contents were not verified in this research. — project file `data/README.md`

### Inferences
- The team's split (3,029 / 3,226 / 4,973) is close to the Tanzanian Sci-Data counts (3,339 / 3,496 / 4,932). It is probably a cleaned or merged derivative, with "otra" taking the place of Fusarium wilt. The team should state the exact provenance and the licence (CC BY 4.0 requires attribution).
- A training set where "other condition" is mostly Fusarium wilt imagery will not cover Mexican confounders: nutrient deficiency, mechanical damage, senescence, Cordana, Yellow Sigatoka. This is a concrete dataset gap the team could fill.
- The Colombian UAV RGB dataset (CC BY 4.0) is the most relevant external test set for checking cross-farm and cross-sensor generalisation of a drone model.

### Gaps
- Licences for the Mendeley sets, and BananaLSD's per-class counts, were not verified from the repository pages (JavaScript-rendered, and the API was unavailable).
- No open dataset with Stover/Gauhl severity grades or Fouré stage labels was found.
- No Mexican or Central American open RGB Sigatoka dataset was found.

---

## Q3. Domain shift (public close-ups vs field/drone images) and how papers handle it

### Takeaway
Domain shift is the single most cited weakness. The canonical result: a PlantVillage-trained model fell from 99.35% to about 31% on images taken under other conditions. Banana-specific papers rarely measure it. Mitigations in the literature:
- training on field and multi-region data (Tumaini);
- human-in-the-loop feedback;
- few-shot cross-domain learning;
- background cropping;
- stating explicitly that external validation is still missing.

### Cited Findings
- **Mohanty et al. 2016, Frontiers in Plant Science 7:1419** (pre-2019 baseline). Trained on 54,306 lab-condition images, the model reached 99.35% on held-out data. On images from trusted online sources it got "an overall accuracy of 31.40% in dataset 1, and 31.69% in dataset 2", and accuracy "is reduced substantially, to just above 31%". — [doi:10.3389/fpls.2016.01419](https://doi.org/10.3389/fpls.2016.01419); [PMC5032846](https://pmc.ncbi.nlm.nih.gov/articles/PMC5032846/)
- **Quijije et al. 2026.** Lists as limitations:
  - training data from Tanzania and Bangladesh, not Ecuador;
  - no plant-, plot-, farm- or device-level identifiers, so validation by biological unit was impossible;
  - fixed HSV thresholds that may fail under other lighting or cultivars;
  - CNNs that "may be exploiting dataset-specific cues or backgrounds";
  - confusion with nutrient deficiency or water stress. — [doi:10.3389/frai.2026.1861135](https://doi.org/10.3389/frai.2026.1861135)
- **Mora et al. 2025.** Organised ground-level data by region (Africa, Latin America, India, Asia, Australia) and reported per region. Leaf-level mAP was the lowest across plant parts (healthy leaf 0.60–0.71). Human-in-the-Loop AI is used for "continuous model improvement through user feedback, reducing false positives and negatives". — [doi:10.1038/s41598-025-87588-2](https://doi.org/10.1038/s41598-025-87588-2)
- **Yang et al. 2024, Frontiers in Plant Science** ("From laboratory to field: cross-domain few-shot learning for crop disease identification in the field"). States that lab-trained classifiers "suffer significant performance degradation" in the field. The proposed CDFSL-BDC (ResNet-18 + CBAM + Brownian distance covariance) reached 77.42% (5-way 5-shot) and 62.46% (1-shot) going from PlantVillage to a field crop disease dataset; the best case was 80.13% 5-shot. — [doi:10.3389/fpls.2024.1434222](https://doi.org/10.3389/fpls.2024.1434222); [PMC11688362](https://pmc.ncbi.nlm.nih.gov/articles/PMC11688362/)
- **bioRxiv preprint (2024), "Addressing domain shift in deep learning…".** Cross-dataset drops were consistent across ResNet, EfficientNet, Inception and MobileNet, "confirming that domain shift … cannot be resolved by merely altering the model architecture" **[snippet-only]**. — [bioRxiv 10.1101/2024.10.07.617111](https://www.biorxiv.org/content/10.1101/2024.10.07.617111v1.full)
- **Sustainability 2026 (non-banana).** Accuracy fell to 61.97% on real field images, attributed to domain shift; over-reliance on PlantVillage is said to inflate reported metrics **[snippet-only]**. — [doi:10.3390/su18136867](https://doi.org/10.3390/su18136867)
- **Jiménez et al. 2025 (Ecuador).** Heavy augmentation (900 → 9,000 images) "did not significantly improve" accuracy. — [doi:10.3390/ai6030061](https://doi.org/10.3390/ai6030061)
- **Linero-Ramos 2024** frames its own drone dataset as a way to "enhance and scale up the current approach using RGB images obtained by conventional cameras and even smartphone cameras, available in open datasets". It treats public phone data as insufficient for drones. — [doi:10.3390/drones8090503](https://doi.org/10.3390/drones8090503)
- **Oviedo 2025.** Occluded and cluttered canopy produces mixed Moko / Black Sigatoka predictions. — [Technologies 2025](https://doi.org/10.3390/technologies13090382) (via search summary of the article)

### Inferences
- The team's error analysis is credible and aligned with the literature. The dominant error (16% of "sana" predicted as "otra") was traced to noisy HEALTHY labels in the public set. The team's own conclusion is to stop iterating on public data and collect expert-validated field data.
- The team's ZED X Mini drone frames will differ from cropped phone close-ups in scale, viewing angle, motion blur, canopy background and lighting. A drop like Mohanty's or Mora's is expected until field data is added.
- Credible fixes that need no new hardware:
  1. A held-out field test set split by farm and date (no plant-level leakage).
  2. Fine-tuning on reviewed field images through the existing review queue (the human-in-the-loop approach of Mora 2025).
  3. Leaf/tile cropping before classification.
  4. Reporting per-condition metrics: sun/shade, altitude, leaf age.

### Gaps
- No banana study was found that quantifies a phone-to-UAV transfer drop (train on close-ups, test on drone tiles).
- No banana study was found that uses self-supervised pretraining or test-time adaptation.

---

## Q4. Lightweight / edge models and reported on-device speeds

### Takeaway
Banana papers favour MobileNet, SqueezeNet, EfficientNet-B0 and small YOLO models. On-device numbers are scarce and coarse: "<5 s per image" on a phone, "≥15% faster" on a Jetson Xavier. Vendor benchmarks show nano YOLO models running in single-digit milliseconds with TensorRT FP16 on a Jetson Orin Nano Super.

### Cited Findings
- **Selvaraj 2019** evaluated SSD MobileNetV1 "with a future view to run these detection capabilities on a mobile device". MobileNetV1 trailed ResNet50 and InceptionV2 in accuracy. — [doi:10.1186/s13007-019-0475-z](https://doi.org/10.1186/s13007-019-0475-z)
- **Sanga 2020** chose InceptionV3 (95.41%) over ResNet152 (99.2%) for the phone because it "demands much less memory". — [doi:10.48084/etasr.3452](https://doi.org/10.48084/etasr.3452)
- **Elinisa & Mduma 2024:** the mobile CNN classifies in under 5 seconds per image **[snippet-only]**. — [doi:10.1016/j.atech.2024.100423](https://doi.org/10.1016/j.atech.2024.100423); [DOAJ](https://doaj.org/article/ed658bfba39341b98a3dadd7916babdd)
- **Nassor et al. 2024:**
  - MobileNetV2: the smallest model, at 2.51 MB.
  - SqueezeNet: the best accuracy, at 97.12%.
  - MobileNetV3-small: 14 MB; trained fastest (2.465 min).
  - SqueezeNet: trained slowest (14.76 min). — [doi:10.1088/1755-1315/1359/1/012010](https://doi.org/10.1088/1755-1315/1359/1/012010)
- **BananaSqueezeNet 2023** is billed as "very fast, lightweight" and beats EfficientNetB0, MobileNetV3 and ResNet-101 in accuracy (0.9625). — [doi:10.1016/j.atech.2023.100214](https://doi.org/10.1016/j.atech.2023.100214)
- **EF-CenterNet 2025** (UAV banana leaf disease): ≥2.09× fewer parameters and ≥3.18× fewer GFLOPs than competitors, and the highest processing rate on a Jetson Xavier (≥15% better). — [doi:10.1016/j.compag.2025.109927](https://doi.org/10.1016/j.compag.2025.109927)
- **Quijije 2026** reports MobileNetV3 at 0.96 accuracy on a 3-class public set, the same as ResNet-18 and EfficientNet. Small models are not worse on these data. — [doi:10.3389/frai.2026.1861135](https://doi.org/10.3389/frai.2026.1861135)
- **Du et al. 2026** reports its hybrid (98.28% accuracy) at 12.7 M trainable parameters. — [doi:10.1038/s41598-026-47092-7](https://doi.org/10.1038/s41598-026-47092-7)
- **Ultralytics Jetson guide, Orin Nano Super, YOLO26n detection at 640 px** (Ultralytics 8.4.33; times exclude pre/post-processing):

  | Format | Inference time (ms/image) | mAP50-95 |
  |---|---|---|
  | PyTorch | 15.60 | 0.4790 |
  | ONNX | 15.76 | 0.4760 |
  | TensorRT FP32 | 7.53 | 0.4770 |
  | TensorRT FP16 | 4.57 | 0.4800 |
  | TensorRT INT8 | 3.80 | 0.4490 |

  No -cls benchmarks and no standard Orin Nano (non-Super) table are given. — [Ultralytics docs](https://docs.ultralytics.com/guides/nvidia-jetson/)
- **Non-banana but related lightweight YOLO work:** ELM-YOLOv8n for apple leaves in complex orchards (Frontiers Plant Sci 2025). — [doi:10.3389/fpls.2025.1545875](https://doi.org/10.3389/fpls.2025.1545875)

### Inferences
- YOLOv8n-cls at 384 px is a reasonable, literature-consistent choice. The Orin Nano's compute budget is not the bottleneck. Exporting to TensorRT FP16 should give the largest speed-up with no measurable accuracy loss (FP16 mAP equals FP32 in the vendor table). INT8 costs accuracy and needs a calibration set. This is extrapolated from detection benchmarks.
- The spare compute could pay for more robust inference: tiling or leaf cropping, test-time augmentation, an ensemble, or a small detector/segmenter (YOLOv8n-seg / YOLO11n-seg) for per-lesion localisation. These are software-only changes.

### Gaps
- No published on-device latency was found for any banana model on a Jetson Orin Nano. None was found for YOLOv8n-cls / YOLO11n-cls on a Jetson either. Benchmarking it would itself be a small, credible contribution.
- No banana study was found that reports quantised (INT8 TFLite/TensorRT) accuracy versus FP32.

---

## Q5. Severity estimation and early-stage (stage 1–2 streak / pre-symptomatic) detection from RGB

### Takeaway
Reliable pre-symptomatic Black Sigatoka detection has been shown only with hyperspectral imaging under controlled inoculation (about 98% accuracy). RGB work on stages or severity is limited and weakly validated:
- 4-stage CNN: 89% validation accuracy, low-tier journal.
- ResNeXt50 seriousness grading: 95.53%, conference paper, snippet only.
- LeNet + decision tree severity (2021) and a histogram-segmentation phone app for % affected area (2020).

Human severity scoring is itself noisy. Stover/Gauhl raters tend to overestimate, and a 2024 standard area diagram (SAD) improves rater agreement.

### Cited Findings
- **Ugarte Fajardo et al. 2020, Applications in Plant Sciences 8(8):e11383.** Hyperspectral imaging (386–1019 nm) of inoculated 3-month-old plants. A PLS-PLR model predicted disease presence with 98% accuracy, validated by leave-one-out and external validation. Key wavelengths were 577–651 nm and 700–1019 nm. It "effectively estimated the presence of black Sigatoka disease at the early stages". — [doi:10.1002/aps3.11383](https://doi.org/10.1002/aps3.11383)
- **Ugarte Fajardo et al. 2022, Plants 11(19):2581.** On hyperspectral images of inoculated leaves, PLS-PLR, SVM and MLP allow "successful detection of black sigatoka disease with high accuracy" for early detection — [doi:10.3390/plants11192581](https://doi.org/10.3390/plants11192581).
  - A search summary added that classification was low at early stages and exceeded 95% once infected area passed 6% of the leaf **[snippet-only, not verified in full text]**.
- **Kambo et al. 2024** (RGB, 4 stages: healthy, early, intermediate, advanced): basic CNN at 89% validation accuracy and macro P/R/F1 ≈ 0.90; VGG16 F1 0.75. — [doi:10.17485/ijst/v17i37.2453](https://doi.org/10.17485/ijst/v17i37.2453)
- **Escudero et al. 2021** (RGB): a LeNet patch detector plus a decision tree for "level of infection severity". — [doi:10.18178/ijmlc.2021.11.4.1055](https://doi.org/10.18178/ijmlc.2021.11.4.1055)
- **Tovar-Martínez et al. 2020, Visión Electrónica 14(1):111–118** (Colombia). A phone app segments diseased pixels by histogram analysis to compute "percentage of affected area". It was validated by RMS error against manual segmentation, with usability and response-time tests. — [doi:10.14483/22484728.15906](https://doi.org/10.14483/22484728.15906)
- **Singh et al. 2024 (IEEE conference):** ResNeXt50, 5 seriousness levels, 10,000 photos, 95.53% **[snippet-only]**. — [doi:10.1109/iatmsi60426.2024.10503074](https://doi.org/10.1109/iatmsi60426.2024.10503074)
- **Elinisa et al. 2024:** U-Net lesion segmentation, Dice 96.45% and IoU 93.23%. Pixel masks of this kind are the basis for computing % necrotic area. — [doi:10.1080/08839514.2024.2440837](https://doi.org/10.1080/08839514.2024.2440837)
- **Pinzón-Núñez et al. 2024, European Journal of Plant Pathology 170(3):535–548.** New SAD for black leaf streak with grades 0 (0%), 1 (0.1–5.0%), 2 (5.01–13.0%), 3 (13.01–23.0%), 4 (23.01–40.0%), 5 (40.01–65.0%) and 6 (>65.0%). Thirteen evaluators gained precision, accuracy, repeatability and reproducibility compared with another SAD. — [doi:10.1007/s10658-024-02917-x](https://doi.org/10.1007/s10658-024-02917-x)
  - Per the article page, Stover's scale as modified by Gauhl is the worldwide standard. Evaluators tended to overestimate with it, and "only 38% of the evaluators that used Stover's scale presented R² values > 0.80" **[snippet-only]**. — [Springer page](https://link.springer.com/article/10.1007/s10658-024-02917-x)
- **Quijije 2026:** "the current data do not establish physiological early infection detection". — [doi:10.3389/frai.2026.1861135](https://doi.org/10.3389/frai.2026.1861135)
- **Calou 2020** quantified Yellow Sigatoka spread from monthly UAV RGB flights and compared it with traditional field evaluation. This is a severity-mapping use case. — [doi:10.1016/j.biosystemseng.2020.02.016](https://doi.org/10.1016/j.biosystemseng.2020.02.016)

### Inferences
- From a 3-channel RGB camera, the team should not claim pre-symptomatic detection. Stage 1–2 streaks are millimetre-scale, and the only validated early-detection evidence is hyperspectral. A credible claim is detection of visible symptoms plus a severity proxy.
- A practical severity path:
  - lesion or necrosis segmentation (U-Net-style, or YOLO-seg at drone scale);
  - % leaf area affected;
  - mapping to the 2024 SAD grades or to Stover/Gauhl grades;
  - validation against SAD-assisted expert scores, reported as Lin's concordance or R², not just accuracy.

  The team's data schema already has a `severidad_stover` field (docs/05-datos-dataset.md).
- Severity labels from untrained raters will be noisy. Using the SAD during field labelling directly addresses a documented weakness.

### Gaps
- No RGB study with rigorous, field-validated Stover/Gauhl or DSI (disease severity index) estimation was found.
- No RGB detection rates by Fouré stage (1–6) were found.
- The ResNeXt50 and Plants 2022 early-stage numbers could not be confirmed from full text.

---

## Q6. Most-cited limitations / open problems a student project could credibly address

### Takeaway
The recurring gaps:
- no independent field validation, and no farm- or region-level splits;
- domain shift from close-ups to field and canopy views;
- a lack of UAV RGB Sigatoka data, especially from Latin America and Mexico;
- confounders (other leaf spots, nutrient or water stress, occlusion);
- no validated severity estimation;
- few real edge-latency reports;
- little human-in-the-loop or farmer-facing validation.

Each can be addressed with software, data and evaluation work on the team's fixed hardware.

### Cited Findings
- **Lack of independent or operational validation; dataset-specific cues; no plant/farm/device IDs** — [Quijije et al. 2026](https://doi.org/10.3389/frai.2026.1861135)
- **Lack of large annotated banana datasets** is a "major challenge" — [KHO-YOLOv8 preprint 2025](https://doi.org/10.21203/rs.3.rs-6812770/v1)
- **Season coverage:** the 2022 Tanzanian dataset "did not fully represent data from all farming seasons" — [Mduma & Elinisa 2025](https://doi.org/10.1038/s41597-025-04456-4)
- **Occlusion and overlapping symptoms in UAV canopy imagery** — [Oviedo et al. 2025](https://doi.org/10.3390/technologies13090382)
- **Leaf-level detection is the weakest plant part:** healthy-leaf mAP 0.60–0.71. The authors call for "more specific tuning and advanced training techniques to handle higher variability". Human-in-the-loop is used to reduce false positives and negatives. The integration of human-in-the-loop with UAV surveillance for banana "remain[s] underexplored" — [Mora et al. 2025](https://doi.org/10.1038/s41598-025-87588-2)
- **Human severity scoring is subjective:** Stover/Gauhl raters overestimate; the SAD improves agreement — [Pinzón-Núñez et al. 2024](https://doi.org/10.1007/s10658-024-02917-x)
- **Early detection reliably shown only with hyperspectral imaging** — [Ugarte Fajardo et al. 2020](https://doi.org/10.1002/aps3.11383)
- **Lab-to-field degradation is general and architecture-independent** — [Mohanty et al. 2016](https://doi.org/10.3389/fpls.2016.01419); [Yang et al. 2024](https://doi.org/10.3389/fpls.2024.1434222); [bioRxiv 2024 preprint](https://www.biorxiv.org/content/10.1101/2024.10.07.617111v1.full)
- **Smallholder framing:** Tumaini targets "millions of banana farmers in developing countries" with mobile tools — [Selvaraj 2019](https://doi.org/10.1186/s13007-019-0475-z). Integrating UAVs with AI smartphone apps "holds promise for developing advanced early warning systems" — [Mora et al. 2025](https://doi.org/10.1038/s41598-025-87588-2)

### Inferences
These are the contributions a student team could credibly claim, ranked by how much they strengthen the paper or demo:
1. **The first independent field evaluation of a public-data Sigatoka model on Mexican farms.** Test set split by farm and date, expert-verified; report the drop from the 91.8% public-data figure honestly, with per-class recall and confidence intervals.
2. **An open, georeferenced Mexican field dataset** (drone + ground photos) with expert labels and SAD/Stover severity, released under CC BY. No such dataset was found.
3. **Measured domain-shift mitigation:** fine-tune on reviewed field images from the existing review queue (human-in-the-loop as in Mora 2025). Show accuracy against the number of reviewed images (a learning curve, like the "dataset scalability" framing in Linero-Ramos 2024).
4. **A confounder-aware "other" class and an abstain / "needs review" option** based on calibrated confidence. This targets the documented confusion with nutrient stress and other leaf spots.
5. **A severity proxy:** a % affected-area estimate from segmentation, mapped to SAD grades and validated with concordance statistics. Explicitly not a pre-symptomatic claim.
6. **On-device benchmarks** of YOLOv8n-cls / YOLO11n-cls (PyTorch, ONNX, TensorRT FP16/INT8) on a Jetson Orin Nano at 384 px. No such banana numbers exist.
7. **Cross-dataset testing** against the Colombian UAV RGB set (Zenodo, CC BY 4.0) and BananaLSD, as external benchmarks.

### Gaps
- No published farmer-usability or adoption study of AI Sigatoka tools for Latin American smallholders was found. The Tumaini field-testing claims come from press releases ("90% success rate"), not from a peer-reviewed field trial.
- Economic or decision value (fungicide-spray decisions informed by AI severity) was not found in the reviewed literature.
