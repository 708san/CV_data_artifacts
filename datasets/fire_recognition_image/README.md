# Fire Recognition Image Dataset — CV lesson format

Original image subset of Mendeley Data v4: 1,112 PNG images, four author-provided scene labels. Image pixels are unchanged; augmented files are excluded.

## Student task

Build a classroom image-classification prototype that sorts example fire-related scenes for a human to review. The labels are the dataset authors’ categories, including `Safe_Fire` and `Artificial_Fire`; they do not mean that an actual scene is safe or unsafe. Do not use the model to decide whether to evacuate, trigger or silence an alarm, or replace adult/emergency guidance.

## Files

- `images/{train,val,test}/{class}/`: original PNGs.
- `labels.csv`: image, author label, and split.
- `metadata.jsonl`: the same fields in JSON Lines form.
- `manifest.json`: source, counts, split, and audit notes.

Class split counts: `{"Artificial_Fire": {"test": 43, "train": 200, "val": 43}, "Fire": {"test": 43, "train": 198, "val": 42}, "Safe_Fire": {"test": 41, "train": 189, "val": 40}, "Smoke": {"test": 41, "train": 191, "val": 41}}`.
