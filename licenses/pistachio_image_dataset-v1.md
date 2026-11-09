# Pistachio Image Dataset v1 — attribution and rights review

## Source and license

Murat Koklu (Mendeley Data contributor), *Pistachio Image Dataset*, version 1, DOI `10.17632/h7pf57cgg9.1`, [Mendeley Data v1](https://data.mendeley.com/datasets/h7pf57cgg9/1). The dataset page displays CC BY 4.0 and describes 2,148 images of Kirmizi and Siirt pistachio samples.

The related 2022 research article states that the Kirmizi and Siirt samples were collected for that study and that the authors created the images with their specially designed computer-vision system. It describes a fixed lighting box and camera setup. The Mendeley contributor Murat Koklu is also listed among the article's authors and data curators. This supports treating the dataset contributor's explicit CC BY 4.0 selection as the license grant for these study-created images. The article itself has a separate license; neither article PDF nor its figures are included in the artifact.

Primary evidence:
- [Mendeley Data v1](https://data.mendeley.com/datasets/h7pf57cgg9/1)
- [Singh et al. (2022), MDPI Electronics](https://www.mdpi.com/2079-9292/11/7/981)
- [Ozkan, Koklu & Saracoglu (2021), Progress in Nutrition](https://www.mattioli1885journals.com/index.php/progressinnutrition/article/view/9686)

## Required attribution

Murat Koklu, *Pistachio Image Dataset*, Mendeley Data v1, DOI: 10.17632/h7pf57cgg9.1, licensed under CC BY 4.0.

The source requests citation of these related works:
- Ozkan, I. A., Koklu, M., & Saracoglu, R. (2021). “Classification of Pistachio Species Using Improved K-NN Classifier.” *Progress in Nutrition*, 23(2). DOI: 10.23751/pn.v23i2.9686.
- Singh, D., Taspinar, Y. S., Kursun, R., Cinar, I., Koklu, M., Ozkan, I. A., & Lee, H.-N. (2022). “Classification and Analysis of Pistachio Species with Pre-Trained Deep Learning Models.” *Electronics*, 11(7), 981. DOI: 10.3390/electronics11070981.

## Changes and scope

The artifact places images in the common `images/<split>/<class>/` layout and includes `labels.csv`, `metadata.jsonl`, and a manifest. It uses deterministic class-stratified train/validation/test splits with seed 42 (1,503/322/323). Image pixels are unchanged. Ten non-image source files, including feature tables and citation documents, are excluded.

The fixed source ZIP (27,859,492 bytes, SHA-256 `140760707018b7f53d91a86a1d7be96d92b1a0d26a75690ab9280ed1170df895`) was verified before safe extraction. All 2,148 JPEG files decoded as 600×600 RGB; no exact duplicates were found. Four representative images were visually reviewed and showed isolated pistachio samples on a black background. This sample review is not a full manual image review. The study describes a controlled camera setup and images created by the research authors; the review found no reason to expect third-party photographs, people, or packaging in the dataset. No independent rights-transfer document was reviewed; redistribution relies on the contributor's displayed CC BY 4.0 grant and the study authors' image-creation statement.

The prepared artifact is for educational classification only. It does not establish food quality, freshness, safety, or commercial value.
