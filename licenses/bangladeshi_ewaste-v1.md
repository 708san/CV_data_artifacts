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

整形artifact：v0.1.0、2,157画像・12クラス。出典ZIPのSHA-256を照合後、YOLO bboxは保持し、polygonは軸に平行な外接矩形へ変換します。変換後の画像画素は変えていません。artifact ZIPのサイズとSHA-256は`manifests/bangladeshi_ewaste-v0.1.0.json`に記録します。

## 残る制約

CC BYのデータライセンス表記は、画像内に写る商標など第三者の別権利まで許諾するものではありません。製品ロゴが見えるため、ブランド識別や推薦の教材には使いません。Medical Wasteなどのラベルも実際の分別・処理・危険物取扱い判断に使わない教材説明を付けます。上流データの撮影者・データ提供者によるCC BY付与を根拠に評価していますが、Mendeley以外の個別素材許諾書は収録されていません。

全2,157画像を22枚のコンタクトシートで目視し、代表画像も確認しました。対象物はラベルと概ね整合し、人物の写り込みは見つかりませんでした。製品ロゴが見える画像は残るため、ブランド識別・推薦には使いません。Medical Wasteを含むラベルは医療廃棄物の判定、分別、取扱いの根拠になりません。バングラデシュ由来の物品画像であり、日本の自治体ルールを示すものでもありません。高校生には「身近な電子機器・廃棄物の画像を分類する試作教材」として使えます。

公開可否はMendeleyのCC BY 4.0表示と、ZIP内の同ライセンス表示に基づきます。個別ロゴ等の別権利を許諾済みとは扱いません。変更点・帰属表示・注意事項はartifact内`LICENSE.md`にも記載します。
