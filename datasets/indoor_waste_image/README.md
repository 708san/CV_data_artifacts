# Indoor Waste Image Dataset — CV lesson format

This archive is a fixed, student-friendly packaging of the Mendeley Data v1 dataset. It contains 4,000 images (1,280×720), four classes, and 6,968 bounding boxes. The images are unchanged.

## Student task

Use object detection to find paper, plastic, caps, and shells left on indoor floors. For example, students can make a prototype that marks areas for a cleaning check after an event. The model only points out possible objects; a person confirms the location and local waste rules. It is not an autonomous cleaning or safety system.

## Files

- `images/{train,valid,test}/`: source JPEGs, unchanged.
- `labels/{train,valid,test}/`: YOLO normalized `class_id x_center y_center width height` labels.
- `annotations.jsonl`: normalized annotation records, one per image.
- `metadata.jsonl`: image, label, split, and box count.
- `classes.json`: class IDs and Japanese names.
- `manifest.json`: source hashes, split method, and transformation record.

Frames from the same source video are kept in one split. Split counts: `{"train": 2765, "valid": 685, "test": 550}`. 380 source boxes extended outside the 1,280×720 image by at most 1 pixel; those coordinates were clamped to image edges. No image pixels were changed.
