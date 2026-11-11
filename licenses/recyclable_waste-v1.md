# Recyclable Waste Image Dataset v1 — attribution and review

Source: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, https://data.mendeley.com/datasets/h5pxbsdz4m/1. The Mendeley page displays CC BY 4.0 and states the public release contains only images collected by the author; images from third-party datasets were excluded from this public subset.

Required attribution: João Alves (2026), *Recyclable Waste Image Dataset*, Mendeley Data v1, DOI `10.17632/h5pxbsdz4m.1`, CC BY 4.0.

Artifact v0.1.1 is derived from the fixed v0.1.0 prepared artifact (SHA-256 `39c52710ddaeb4e662dbbf3ba7cd95725a8b11cf2b22434d04bc52626b721299`). The original preparation excluded 12 exact duplicate source files; applied EXIF orientation; resized and re-encoded images as JPEG at up to 512 pixels on the longest side; removed source metadata; and added a deterministic class-stratified split (seed 42). During full-set visual review of the 977 prepared images, one paper-category image showing a political campaign poster with a person's portrait was excluded. The remaining 976 processed image files are byte-for-byte unchanged from v0.1.0.

Technical audit: all 989 publicly listed image files matched their recorded sizes and SHA-256 values and decoded successfully. The landing page claims 1,000 images; 989 are listed in the public API. 104 source images contain GPS data in EXIF; the prepared data removes embedded metadata. The official page states that the public set contains only images collected by the author and excludes images from third-party datasets.

Do not use this dataset to automate real-world waste-sorting decisions. Category counts are highly imbalanced. Product/brand packaging marks remain incidental and do not imply endorsement.

## 2026-11-09 redistribution review

The Mendeley v1 page displays CC BY 4.0, identifies the author, and states that the public image set contains images collected by that author, excluding images from third-party datasets. Redistribution is approved within that license scope with attribution and a notice of preparation changes. A thumbnail contact-sheet review covered all 977 prepared images: class contents broadly matched, no photographed bystander was apparent, and product branding/package text was visible. One discarded-paper image showed a political campaign poster with a person's portrait and political messaging; it was excluded from v0.1.1. This review does not provide legal clearance for trademarks. Do not imply endorsement by any visible brand.

The v0.1.0 prepared ZIP had 977 images. The derived v0.1.1 ZIP has 976 images and 981 files. ZIP CRC and every file size/SHA-256 match the v0.1.1 manifest. ZIP SHA-256: `c209fac02eb88867bdc709b33e46f1d1ccd9ac63859ead5add112b8a4d8ac2f5`; size 93,564,328 bytes. The fixed Release asset will be uploaded after this manifest PR is merged.
