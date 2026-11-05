# Manifests

各GitHub Release assetの取得条件をJSONで記録します。

最低限、次の項目を含めます。

```json
{
  "dataset_id": "example",
  "artifact_version": "v1.0.0",
  "artifact_url": "https://github.com/708san/CV_data_artifacts/releases/download/...",
  "artifact_sha256": "",
  "source_url": "https://example.org/original",
  "source_version": "",
  "source_sha256": "",
  "license": "",
  "rights_status": "approved_for_redistribution",
  "attribution": "",
  "modifications": [],
  "transform_version": ""
}
```

空の雛形は登録データを意味しません。実データを公開するReleaseには、空欄のないmanifestを添付します。台帳の形式は[`registry/schema-v1.json`](../registry/schema-v1.json)で検査します。
