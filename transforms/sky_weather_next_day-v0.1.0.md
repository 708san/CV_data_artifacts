# Transform record: sky_weather_next_day v0.1.0

## Input and pinning

- User-provided file: `sky-weather-next-day.zip`
- Input size: 10,014,296 bytes
- Input SHA-256: `c30cf675819fea9b0bad62e0d0c8cb77890b808253e92c604b39d6c97a6f5280`
- Exact upstream image-dataset commit was not present in the archive.

## Output

- 1,000 224×224 JPEGs, grouped at `images/<split>/<class>/`.
- `labels.csv`: classification target, source split, capture/target timestamps, precipitation, cloud cover, snowfall, and provenance columns.
- `metadata.jsonl`: common image/label/split index.
- `manifest.json`: class names, split counts, source note, and types for extra metadata columns.
- Original JPEG bytes are preserved.

## Checks performed

- ZIP member paths and symlink entries: no unsafe entries found.
- ZIP CRC: passed.
- All 1,000 JPEGs decoded; all are 224×224.
- CSV rows and image references: 1,000 rows, no missing references, duplicate paths, or duplicate image bytes.
- Capture-date consistency: no conflicting labels per capture day; each day belongs to one split.
- Target dates follow capture date + 1 day.
- 5 representative images visually reviewed as all-sky imagery.
- Class counts: sunny 664, cloudy 184, rainy 152.
- Split counts: train 656, val 161, test 183.

## Known limitation

Split class proportions differ substantially, particularly rainy. Source imagery comes from one station in Golden, Colorado, and weather labels are ERA5 reanalysis, not official forecast observations. The user archive does not record an upstream source revision.
