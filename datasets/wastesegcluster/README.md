# WasteSegCluster — CV lesson format

A fixed-version packaging of the Mendeley Data v4 images and annotations: 1,947 images and 3,900 waste instances across four classes. Images are copied unchanged.

## Student task

Use object detection to mark visible waste along waterways, then summarize where cleanup should begin. This dataset was collected around Dhaka, Bangladesh. Students should compare with their own local photos before applying results to a local site; the model output is a survey aid, not a water-quality or public-health measurement.

## Files

- `images/{train,valid,test}/`: source JPEGs, unchanged.
- `labels/{train,valid,test}/`: normalized YOLO bounding boxes.
- `annotations.jsonl`: one normalized box record per image.
- `metadata.jsonl`: image, label, split, and box count.
- `classes.json`: class IDs and Japanese names.
- `manifest.json`: counts and conversion details.

The source provides polygons and bounding boxes in COCO format. This student package uses only bounding boxes, so it is for object detection rather than mask segmentation. The unused parent category in the source COCO metadata has zero instances and is omitted. One image has no annotations; its empty label file means no box was supplied, not a guarantee that the scene is waste-free.
