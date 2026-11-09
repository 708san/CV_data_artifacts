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

`recyclable_waste` v0.1.0は、Mendeley Data v1の989画像を全件SHA-256照合・デコードし、完全一致重複を除いた977画像で共通形式artifactを準備しました。元画像にGPS情報が含まれていたため、派生画像はEXIF等を除去しています。全画像の人手によるプライバシー・権利確認が残っているため、`registry/datasets.json`とReleaseには登録していません。詳細は監査reportとライセンス記録を参照してください。

`pistachio_image_dataset` v0.1.0 has passed full artifact-manifest verification. The Mendeley v1 page displays CC BY 4.0, and the related 2022 article states that its authors created the study images with their computer-vision system. Redistribution is approved with attribution and the two requested citations; the article itself is not included. Fixed Release asset `pistachio_image_dataset-v0.1.0` is published and its URL/SHA-256 are in `registry/datasets.json`. The exact license basis and review limits are recorded in the license file and audit report.
