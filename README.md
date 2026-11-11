# CV_data_artifacts

高校生向けCV教材で利用する、許諾済みデータの保管・配布用リポジトリです。

このリポジトリには、ライセンスと再配布条件を確認したデータだけを、バージョン付きのGitHub Release assetとして登録します。通常のGit履歴には大容量の画像やLoRA素材をコミットしません。

## 役割分担

- `CV_data`：Pythonライブラリ、取得API、変換処理、テスト、候補台帳
- `CV_data_artifacts`：許諾済みの原本・派生データのmanifestとRelease配布物
- PyPI：`cvlesson`のコードとデータ取得仕様

## 登録条件

データを追加する前に、次を満たします。

1. 出典、固定版、元ファイルのSHA-256を記録する。
2. 画像・アノテーション・キャプションごとの権利を確認する。
3. 教材利用と再配布を別々に判定する。
4. 改変内容、変換スクリプト、派生データのライセンスを記録する。
5. 画像・ラベル・マスクの対応を検査する。
6. 公開Release assetのSHA-256をmanifestに記録する。

権利確認中のデータ、`CV_sample_data`から許可なくコピーしたデータ、LoRA重みは登録しません。

## ディレクトリ

```text
registry/       登録データと公開状態の台帳
manifests/      Release assetごとの機械可読manifest
licenses/       出典・クレジット・利用条件の記録
transforms/     派生データを作る変換仕様と検査手順
reports/        実体監査の要約
```

画像やLoRA素材の追加は、対応するmanifest・ライセンス記録・監査レポートがそろった変更で行います。

`manifests/`と`reports/`に準備中の候補があっても、`registry/datasets.json`に登録されていないものは公開済みではありません。Release assetの作成とartifact URL・SHA-256の登録が完了するまで、ライブラリから利用可能とは案内しません。

## 準備中の候補

`recyclable_waste` v0.1.1 is published and registered. It contains 976 images after exact duplicate removal and exclusion of a paper image showing political campaign material and a person's portrait. Source license, attribution, privacy checks, and limitations are in its license record and audit report.

`pistachio_image_dataset` v0.1.0 has passed full artifact-manifest verification. The Mendeley v1 page displays CC BY 4.0, and the related 2022 article states that its authors created the study images with their computer-vision system. Redistribution is approved with attribution and the two requested citations; the article itself is not included. Fixed Release asset `pistachio_image_dataset-v0.1.0` is published and its URL/SHA-256 are in `registry/datasets.json`. The exact license basis and review limits are recorded in the license file and audit report.

`smallfishbd` v0.1.1 is published as a fixed Release asset and registered in `registry/datasets.json`. It contains 1,697 images across ten classes. All 1,700 source images were checked in contact sheets; this does not establish individual image rights. Attribution and the required change notice are included in the artifact. The source and license review are documented in `licenses/smallfishbd-v2.md` and the audit reports.

`food_waste_bangladesh` v0.1.1 is published as a fixed Release asset and registered in `registry/datasets.json`. It contains 633 images after excluding 11 images showing partial people and one image with a QR-code-like mark. Incidental product and venue marks remain visible on some tableware; the artifact states that they do not imply endorsement. The labels describe collection contexts and do not measure waste quantities. See the license record and full audit report for scope and limitations.

`road_traversing_knowledge` v0.1.0 contains 701 paired road images and class-ID masks from Mendeley Data v1. Source PNG pixels and the official train/validation split are preserved. The dataset is suitable for an educational road-environment segmentation task; see its license record for the third-party-content caveat and geographic limits.

`geoset_ennea` v0.1.0 is published and registered with 136 images, 1,188 bounding-box annotations, and 9 classes. The source archive was fully audited; only original photographs were retained, and scenes were split by group. See the audit and license record for scope and caveats.

`bangladeshi_ewaste` v0.1.0 contains 2,157 images across 12 classes. It is prepared as a fixed, reproducible object-detection artifact from the Mendeley v1 CC BY 4.0 source. See its license record and audit report for limitations.

`pust_cafeteria_food` v0.1.0 is published and registered as a 691-image, 16-class educational object-detection artifact from Mendeley Data v2. Its fixed Release asset is available to the library. See its license record and audit report for the source, transformations, and limitations.

`fashion_mnist` v0.1.0 contains 70,000 28×28 grayscale garment-category images under the source repository’s declared MIT license. The artifact preserves grayscale pixel values, separates a deterministic validation split from official training data, and retains the official test split. It is an introductory benchmark and does not classify real-world garment condition, size, brand, or reuse suitability. See the license record, source manifest, and audit report.

`fabricspotdefect` v0.1.0 is published as an original-image-only object-detection artifact from Mendeley Data v1 under CC BY 4.0. It supports educational prototypes for noticing visible spots before washing. The labels do not establish clothing cleanliness, wearability, safety, stain-removal success, or textile quality. See its license record, manifest, and audit report.

`bdroadsigns` v0.1.0 contains 5,136 images in 18 categories from the Mendeley v1 `Compress Dataset` variant. It is for classroom sign-recognition and sign-literacy projects; the Bangladeshi signs do not represent Japanese traffic rules or real-world navigation. See the license record, manifest, and audit report.

`orange_fruit` v0.1.0 is published as a fixed 15,000-image CC BY 4.0 classification artifact. It is suitable for student experiments about visual categories and image conditions in a food-waste discussion; labels do not establish freshness, edibility, food safety, or plant disease. See its license record and audit report.
