# 利用条件・帰属表示

Yi Xian Wang (2025), “Obstacles Avoidance Assistance for Visually Impaired,” Mendeley Data v1, DOI: [10.17632/xwhnp82rhk.1](https://doi.org/10.17632/xwhnp82rhk.1), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

配布元の説明では、画像は公開Roboflowデータセットから選定され、著者がYOLO形式で注釈を付けています。配布元ページはデータセット全体にCC BY 4.0を表示しています。ページ上では、元Roboflowデータセットごとの識別子・ライセンス一覧は示されていません。このartifactは配布元ページの明示したライセンス表示に基づき、上記出典と変更内容を付して再配布します。

## 変更内容

- 固定したMendeley Data v1のアーカイブから1,250枚とYOLO bbox注釈1,627件を採用しました。
- 配布元のtrain/valid分割と4クラスを保持し、共通の物体検出形式へ並べ替えました。
- 画像の画素とbbox座標は変更していません。変換前後の画像SHA-256は一致します。
- 元データにtest splitはありません。新しいtest splitは作成していません。
- `annotations.jsonl`, `metadata.jsonl`, `classes.json`, artifact manifestを追加しました。

データの一部を改変・再構成した場合、この変更表示とCC BY 4.0の帰属表示を引き継いでください。元画像・ラベルに含まれる個別の第三者権利や、撮影対象者の許諾を本プロジェクトが別途保証するものではありません。

この画像群は歩道環境の物体検出を練習するためのものです。物体の存在だけから通行の妨げ・危険・バリアフリー適合を決定せず、実際の移動や案内に使う場合は当事者と現地で確認してください。
