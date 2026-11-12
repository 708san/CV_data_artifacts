# AgriFreshNET — CV lesson format

14,084 unique 512×512 RGB images across 24 author-labeled produce-stage classes. The source labels cover fresh, semi-fresh, and rotten stages for eight produce types. Source image bytes are unchanged; 76 files involved in exact duplicates (including cross-class duplicates) were removed.

## Student task

Create a prototype that helps a household or school cafeteria prioritize which produce to inspect first. The model only predicts the dataset’s visual category. Parenthetical day ranges are the source authors’ labels; they are not a measured expiry date, edibility assessment, or food-safety decision. Always inspect food and follow local food-safety guidance.

## Files

- `images/{train,val,test}/{source-class}/`: unchanged source images.
- `labels.csv`: image path, original class label, and split.
- `metadata.jsonl`: same records in JSON Lines format.
- `manifest.json`: source information, counts, split and audit record.

Augmented variants whose filenames share the same base photo were kept together in a split to reduce train/test leakage. All files involved in an exact duplicate group were excluded, including duplicates whose copies had conflicting class labels.
