# FabricSpotDefect v1: license and attribution

## Source

- Title: FabricSpotDefect: An Annotated Dataset for Identifying Spot Defects in Different Fabric Types
- Authors: Sumaya; Farzana Islam; Md. Fahad Monir; Ashraful Islam
- Provider: Mendeley Data, version 1
- DOI: [10.17632/6574nhzm8x.1](https://doi.org/10.17632/6574nhzm8x.1)
- Source archive size: 941,581,889 bytes
- Source archive SHA-256: `2e4fd58488734fe3b888c0c3633ca4d68da76f3a96f1e9bba08ec710645d6ab2`
- License shown on the Mendeley v1 record: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

## Attribution

Sumaya, Farzana Islam, Md. Fahad Monir, and Ashraful Islam (2024), “FabricSpotDefect: An Annotated Dataset for Identifying Spot Defects in Different Fabric Types,” Mendeley Data v1, DOI: [10.17632/6574nhzm8x.1](https://doi.org/10.17632/6574nhzm8x.1), CC BY 4.0.

## Changes

CV_data excluded augmented images, retained the original image pixels and dimensions, mapped source category id 1 (`spot`) to common class id 0, and converted COCO boxes to normalized center coordinates. Twenty-nine boxes extending past an image edge by no more than 0.5 pixel were clipped to the image bounds.

## Scope and limits

The authors describe the images as everyday home fabrics captured with smartphones, including patterned textiles. A sample of nine images was reviewed; this is not a manual review of every image. This dataset supports learning and prototypes that help people notice visible spots before washing. It does not determine cleanliness, wearability, safety, stain-removal success, or textile quality. The images do not represent all clothing or settings.

This prepared artifact is not endorsed by the dataset authors. Third-party marks or designs, if present, remain the property of their respective rights holders.
