# tomato_leaves v1.0.0 — 利用条件記録

## 元データ

- 出典：[Mendeley Data](https://data.mendeley.com/datasets/tywbtsjrjv/1)
- 固定版：v1、DOI `10.17632/tywbtsjrjv.1`
- 元artifact取得元：[CV_sample_data tomato-v1.2.0 Release](https://github.com/708san/CV_sample_data/releases/tag/tomato-v1.2.0)
- 元ZIP SHA-256：`506560a5ce57394fd739fa73ac3b997a2646f87ea04257334dacb54497e0e1fa`
- ライセンス：[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)

## 判断

Mendeley Dataの公式ページでCC0 1.0表記を確認しました。CC0の説明では、法の許す範囲で複製・改変・再配布が可能です。このartifactでは、出典と派生処理を明記し、元画像の画素は変更していません。

CC0は、肖像・プライバシー・特許・商標など別の権利を自動的に消すものではありません。今回の元Release全量画像監査では画像の破損、ラベル不一致、完全一致重複は確認されませんでしたが、権利の無制限な保証や医学的診断用途の保証は行いません。

## 派生物

- データセットID：`tomato_leaves`
- artifact版：`1.0.0`
- 変換版：`classification_v1.0.0`
- 内容：5クラス分類、7,209画像、`labels.csv`と`metadata.jsonl`を共通形式へ正規化
- 変換：画像コピー、ラベル列の標準化、manifest生成、タイムスタンプ固定ZIP化。追加の画素変換なし

公開Releaseを作成する際は、この記録、manifest、監査報告、artifact本体のSHA-256を同じ版として登録します。
