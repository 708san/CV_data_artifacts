# Fresh and Rotten Fruits v1 — attribution and changes

Nusrat Sultana, Musfika Jahan, and Mohammad Shorif Uddin (2022), *Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality*, Mendeley Data v1, DOI: [10.17632/bdd69gyhv8.1](https://doi.org/10.17632/bdd69gyhv8.1). The official Mendeley record states CC BY 4.0.

The source authors report that original images were collected at fruit shops and real fields, and that the fresh/rotten classes were assigned with help from a domain expert at an agricultural institute.

Changes in this prepared version: the separate augmented archive was excluded; seven exact duplicate images were excluded; source orientation was applied; the longest image edge was limited to 512 pixels; images were re-encoded as JPEG quality 86 and source metadata was removed; deterministic stratified train/validation/test splits (seed 42) and `labels.csv` were added.

The source labels are visual research categories. They are not food-safety, health, or edibility assessments. A representative sample of 64 images was visually reviewed; this was not a manual review of every image.
