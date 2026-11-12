# Obstacles Avoidance Assistance v0.1.0 — 権利・帰属記録

- 出典: Yi Xian Wang (2025), [Obstacles Avoidance Assistance for Visually Impaired, Mendeley Data v1](https://data.mendeley.com/datasets/xwhnp82rhk/1), DOI [10.17632/xwhnp82rhk.1](https://doi.org/10.17632/xwhnp82rhk.1)。配布元ページのライセンス欄にCC BY 4.0の表示があることを確認。
- 配布元ページの説明では、公開Roboflowデータセットから画像を選び、YOLO形式の手動注釈を付けたとされています。ページには元Roboflowデータセットの識別子・個別ライセンス一覧がありません。このデータセット自身のCC BY 4.0表示を再配布の根拠として記録し、画像単位の第三者出典が未記載である点も利用者に示します。
- 固定元: Mendeley Data v1、公開固定版URL `https://data.mendeley.com/public-api/zip/xwhnp82rhk/download/1`、84,945,675 bytes、SHA-256 `cc68e314ef6e8aaab3a7b37fe7897528ec7850ca06f0761206dcd4ddf202515a`。
- 出典表示: `Yi Xian Wang (2025), Obstacles Avoidance Assistance for Visually Impaired, Mendeley Data v1, DOI: 10.17632/xwhnp82rhk.1, CC BY 4.0.`
- 変更: 1,250枚とYOLO bbox 1,627件を共通物体検出形式へ再配置し、日本語クラス名、JSONL注釈、manifest、README、帰属表示を追加。元JPEG 1,250枚のSHA-256とbbox座標はすべて一致。元分割train/validとクラスIDを保持。派生artifactもCC BY 4.0で配布し、帰属・変更表示を同梱。
- 用途: 視覚障害のある歩行者の環境を学ぶため、歩道上に写る段差・柵・穴・ポール候補を画像上で示し、人が確認する地図や記録の試作。柵やポールは写っているだけで通行障害とは限らず、画像には通路幅・迂回路・現地状況の判断情報がありません。実際の移動・ナビゲーション・アクセシビリティ判定に単独使用しません。
- 目視: 各クラスの例を含む8画像を確認。歩道、段差、穴状の破損、柵、ポールが写っている。代表画像では明瞭な顔・車両番号を確認しませんでしたが、これは全画像の人物・個人情報調査ではありません。
