# Recyclable Waste Image Dataset v1 — attribution and review

Source: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, https://data.mendeley.com/datasets/h5pxbsdz4m/1. The Mendeley page displays CC BY 4.0 and states the public release contains only images collected by the author; images from third-party datasets were excluded from this public subset.

Required attribution: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, CC BY 4.0.

Artifact v0.1.0 changes: 12 exact duplicate files excluded; the remaining 977 images were decoded, EXIF orientation applied, longest dimension limited to 512 pixels, and JPEG quality 86 used. EXIF, GPS, TIFF and other source metadata were removed. A deterministic class-stratified train/validation/test split (seed 42) was added. Original downloaded source images were not modified.

Technical audit: all 989 publicly listed image files matched their recorded sizes and SHA-256 values and decoded successfully. The landing page claims 1,000 images; 989 are listed in the public API. 104 source images contain GPS data in EXIF. Five representative images were visually reviewed; product/brand marks were visible in some samples, and no people were apparent in those five. A full manual privacy and third-party rights review has not been completed.

Publication remains on hold pending full image privacy and rights review. Do not use this dataset to automate real-world waste sorting decisions. Category counts are highly imbalanced.
