# Recyclable Waste Image Dataset v1 — attribution and review

Source: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, https://data.mendeley.com/datasets/h5pxbsdz4m/1. The Mendeley page displays CC BY 4.0 and states the public release contains only images collected by the author; images from third-party datasets were excluded from this public subset.

Required attribution: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, CC BY 4.0.

Artifact v0.1.0 changes: 12 exact duplicate files excluded; the remaining 977 images were decoded, EXIF orientation applied, longest dimension limited to 512 pixels, and JPEG quality 86 used. EXIF, GPS, TIFF and other source metadata were removed. A deterministic class-stratified train/validation/test split (seed 42) was added. Original downloaded source images were not modified.

Technical audit: all 989 publicly listed image files matched their recorded sizes and SHA-256 values and decoded successfully. The landing page claims 1,000 images; 989 are listed in the public API. 104 source images contain GPS data in EXIF. Five representative images were visually reviewed; product/brand marks were visible in some samples, and no people were apparent in those five. A full manual privacy and third-party rights review has not been completed.

Publication remains on hold pending full image privacy and rights review. Do not use this dataset to automate real-world waste sorting decisions. Category counts are highly imbalanced.

## 2026-11-09 redistribution review

The Mendeley v1 page displays CC BY 4.0, identifies the author, and states that the public image set contains images collected by that author, excluding images from third-party datasets. Redistribution is approved within that license scope with attribution and a notice of the preparation changes above. A thumbnail contact-sheet review covered all 977 prepared images: class contents broadly matched; no clearly identifiable bystander was apparent; product branding/package text and one apparent printed portrait on packaging were observed. This was a content/privacy screen, not a trademark clearance or forensic review. Do not present the dataset as brand recognition or person recognition, and do not imply endorsement by any visible brand.

The v0.1.0 ZIP was rechecked: all 982 files match the artifact manifest by size and SHA-256, and ZIP CRC passed. ZIP SHA-256: `39c52710ddaeb4e662dbbf3ba7cd95725a8b11cf2b22434d04bc52626b721299`. No Release asset has been created.
