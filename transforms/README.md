# Transform specifications

派生データを作る場合は、元データを変更せず、再現可能な変換仕様を記録します。

- 入力アーカイブまたはファイル集合のSHA-256
- 変換コードまたはコミット
- 除外条件
- ラベル・分割の規則
- 生成物のSHA-256
- 変更点と派生データのライセンス

ライセンスが派生物の再配布を許さない場合、変換仕様だけを記録し、画像本体は公開しません。

## 共通形式の方針

| 課題 | 共通配置 | 状態 |
| --- | --- | --- |
| 画像分類 | `images/<split>/<label>/` + `labels.csv` + `metadata.jsonl` | `classification_v1.0.0`を実装済み |
| 物体検出 | `images/<split>/` + `labels/<split>/*.txt` + `classes.json` | `detection_yolo_v1.0.0`を実装、GeoSetEnnea全量監査待ち |
| 領域分割 | `images/<split>/` + `masks/<split>/` + `classes.json` | `segmentation_v1.0.0`を実装、FruitSeg30全量画像監査待ち |
| LoRA素材 | `images/` + `captions.csv`またはJSONL | 権利確認済み素材ができるまでReleaseしない |

検出・分割については、形式を先に固定し、実装済みとは案内しません。各artifactのmanifestで`label_format`と`transform_version`を明示します。

`classification_v1.py`は、固定版を安全に展開した画像分類データを、CV_dataの共通形式へ変換します。

共通形式は、データセットディレクトリ内に次を持ちます。

- `images/<split>/<label>/画像ファイル`
- `labels.csv`（`image,label,label_id,split,sample_id`）
- `metadata.jsonl`
- `manifest.json`
- `README.md`

元画像の内容は変更しません。入力のラベルとファイル配置を検証し、シンボリックリンク・パストラバーサル・重複パスを拒否します。変換後のartifact全ファイルは、manifest v1でサイズとSHA-256を記録します。

Release assetは`tools/package_artifact.py`でタイムスタンプを固定して作成します。これにより、同じ入力から同じZIPを再生成しやすくします。

例：

```bash
python transforms/classification_v1.py \
  /path/to/extracted/tomato-leaves \
  /tmp/tomato-leaves-common-v1.0.0/tomato_leaves \
  --dataset-id tomato_leaves \
  --artifact-version 1.0.0 \
  --source-url https://github.com/708san/CV_sample_data/releases/download/tomato-v1.2.0/tomato-leaves.zip \
  --source-version tomato-v1.2.0 \
  --source-sha256 506560a5ce57394fd739fa73ac3b997a2646f87ea04257334dacb54497e0e1fa \
  --license 'CC0 1.0' \
  --attribution 'Pandianj, Arun; Geetharamanigopal (2019), Mendeley Data, DOI: 10.17632/tywbtsjrjv.1' \
  --manifest-output /tmp/tomato-leaves-common-v1.0.0/tomato_leaves-manifest.json
```
