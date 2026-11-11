# Indoor Plant Varieties v1 rights review

## Source and license

- Dataset: Sajib Bin Mamun; Md Asraful Sharker Nirob; Md Taimur Ahad; Mashreka Akter; Pranta Saha; Md Assaduzzaman (2024), *Indoor Plant Varieties for Computer Vision Applications: A Diverse Image Dataset*, Mendeley Data v1, DOI: [10.17632/ct79299k27.1](https://doi.org/10.17632/ct79299k27.1).
- Fixed source page: https://data.mendeley.com/datasets/ct79299k27/1
- Mendeley Data v1 page displays CC BY 4.0. The dataset description says the images were collected from BADC and nearby nurseries; the article credits dataset collection to the authors.
- The license permits redistribution and adaptation with attribution and change notices. Artifact attribution is included in `LICENSE.md` and `README.md`.

## Educational fit and limits

The seven classes show common potted ornamental plants that students may encounter at home or school. A suitable task is comparing image-based plant variety predictions with careful human observation. The dataset does not support claims about plant toxicity, edibility, disease, care requirements, or safety around pets or people.

## Inspection and changes

- Fixed original archive: 765,167,460 bytes, SHA-256 `c6e3839666e344ca4bb72fa9b09f36605fe8f972c088f0bba72c5dbe06bde2df`.
- All 1,172 JPEGs were decoded. There were no corrupt images. Dimensions: 1,168 images at 3000×3000 and 4 at 720×720; all RGB.
- Eight images per class (56 total) were reviewed in a contact sheet. Samples showed potted plants consistent with their class folders. This was not an exhaustive human review of every image.
- 10 exact duplicate files were found, all within N-Joy Pothos. One copy from each duplicate pair was excluded.
- 1,159 source images contain GPS EXIF metadata. The 1,162 kept images were re-encoded with EXIF metadata removed; the source archive remains unmodified.
- Kept images were resized to a maximum side of 512 pixels with Pillow LANCZOS, re-encoded as JPEG quality 86, and split within each class using seed 42 at approximately 70/15/15 into train/val/test.
- The prepared artifact has 1,162 images and occupies 74,466,644 bytes of image payload before ZIP packaging.

## Remaining limitations

The class labels and species names are those supplied by the dataset authors. This review did not independently verify each plant species or inspect every image for background details. The dataset was collected in Bangladesh and does not represent all cultivars, growing environments, or household plants in Japan.
