# Custom Bangladeshi E-Waste Image Dataset v1 — 利用条件記録

## 元データ

- 出典：[Mendeley Data v1](https://data.mendeley.com/datasets/77383kmdnw/1)
- DOI：`10.17632/77383kmdnw.1`
- 提供者：Tanzila Afrin、Azizul Abedin Azmi
- 固定ファイル：`E-Waste Dataset (2).zip`（Mendeley file ID `ad031b3c-13e5-4913-8cdd-71dccfab980f`）
- 元ZIP SHA-256：`f73b30286225c208e98b34f81eb5ffef7baf79e883039d2087e8db53f6ee284e`
- ライセンス：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。Mendeley公式ページとZIP内`README.dataset.txt`の両方に表示されています。

## 利用判断

CC BY 4.0は、適切なクレジット、ライセンスへのリンク、変更の表示を条件に、複製・再配布・改変を認めています。配布時の帰属表示は次を含めます。

> Tanzila Afrin; Azizul Abedin Azmi, “Custom Bangladeshi E-Waste Image Dataset for Object Detection and Recognition,” Mendeley Data, v1, DOI: 10.17632/77383kmdnw.1, licensed under CC BY 4.0.

派生artifactでは、元のbbox注釈を保持し、polygon注釈1,407件を軸に平行な外接矩形へ変換します。変換によりpolygonの輪郭形状が失われます。README記載のRoboflow export、640×640 stretch resize、auto-contrastは元データの既存処理として明示し、追加の画素処理を行いません。

準備済み共通artifact候補：v0.1.0、71,762,431 bytes、SHA-256 `fe06d5579e3a84010e0e6ccd7d90d8230ca72d5fcd39719d6d6d8731595007fa`。これはRelease未公開のローカル検証成果です。

## 残る制約

CC BYのデータライセンス表記は、画像内に写る商標など第三者の別権利まで許諾するものではありません。製品ロゴが見えるため、ブランド識別や推薦の教材には使いません。Medical Wasteなどのラベルも実際の分別・処理・危険物取扱い判断に使わない教材説明を付けます。上流データの撮影者・データ提供者によるCC BY付与を根拠に評価していますが、Mendeley以外の個別素材許諾書は収録されていません。

現在はライブラリの固定取得APIと生徒向けNotebookが未完了のため、Release公開を保留しています。
