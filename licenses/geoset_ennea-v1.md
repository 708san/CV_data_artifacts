# GeoSetEnnea v1 — 利用条件・出典

## 固定版と一次情報

- 公式データ：[Mendeley Data v1](https://data.mendeley.com/datasets/fg97mhsdbr/1)
- DOI: `10.17632/fg97mhsdbr.1`
- 掲載者：Sakhawat Hossain、Md Sadman Haque、Sadia Islam
- 公式ページのライセンス表示：CC BY 4.0
- 公式ページの説明：9種類の幾何用具、966画像、8,253注釈。画像はバングラデシュ・ダッカの文具店や図書館でスマートフォン撮影。
- 公開APIのファイルID・サイズ・SHA-256の全件目録は `manifests/sources/geoset_ennea-v1.json` に記録済み。この調査では学習用966画像と966ラベルだけを取得し、全ファイルをAPI記載SHA-256に照合した。

## 教材課題との適合

学校の共有コンパス、定規、分度器などを授業前後に画像から見つけ、返却・補充の確認を整理する物体検出の試作に使える。元画像は現地の店舗・図書館を撮影したもので、日本の学校の備品・背景での精度は未検証。実際の在庫判断に使う前に、各校の画像で検証が必要。

## 変換・帰属

- 元の画像とYOLOラベルの内容を変更せず収録。
- ファイル名から識別した撮影・augmentation系列を同じsplitにまとめた。元splitで交差していた81系列の漏洩を避けるため、train/valid/testを676/193/97で再割当て。
- 共通形式の`annotations.jsonl`、`metadata.jsonl`、`classes.json`、説明と本ファイルを追加。
- 元のMetadata.csv（カメラ機種名を含む）と別フォルダのraw/augmented素材は含めない。
- 出典表示：Sakhawat Hossain, Md Sadman Haque, and Sadia Islam, “GeoSetEnnea: A Multi-Class Image Dataset for Object Detection of Geometric Tools,” Mendeley Data, v1, DOI `10.17632/fg97mhsdbr.1`.
- 派生物の公開時は [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)に従い、出典と変更内容を表示する。

## 公開判断

技術検査と教材利用の具体案は整ったが、画像内の商品パッケージ・ブランド表示等の個別第三者権利を確認していない。CC BY表示をこれら第三者要素の利用許可と解釈せず、再配布Release・ライブラリ登録は保留する。データセットの掲載は商品・ブランドの推奨を意味しない。
