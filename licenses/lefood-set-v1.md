# LeFood-Set v1 — 利用条件・出典

## 固定版とライセンス

- 公式データ：[Mendeley Data Version 1](https://data.mendeley.com/datasets/cchsk79jkt/1)、DOI: [10.17632/cchsk79jkt.1](https://doi.org/10.17632/cchsk79jkt.1)
- Mendeley v1のライセンス表示：CC BY 4.0。
- データ提供論文もCreative Commons Attribution Licenseを明記しています。
- 帰属：Sari, Yuita Arum; Wani, Yudi Arimba; Nakazawa, Atsushi (2025), “LeFood-Set: Leftovers Food Dataset”, Mendeley Data v1, DOI: 10.17632/cchsk79jkt.1.
- [CC BY 4.0の条件](https://creativecommons.org/licenses/by/4.0/)

## 教材用派生物の変更

派生artifact v0.1.0は、公式公開APIに列挙された全1,048 JPEGとXLSXを個別のサイズ・SHA-256で確認しました。食前・食後の画像が両方存在する524組だけを含みます。元表の画像欠落154行は除外しました。JPEGの画素データは変更していません。画像ファイル名とフォルダを整理し、CSVへ表を変換して、残量比・重量差・再現可能なペア単位splitを追加しました。重量の前後が逆転する10組は除外せず、weight_order_anomaly列で表示します。全ファイルのSHA-256はmanifestに記録しています。

## 権利・画像内容の確認範囲

全画像を一覧で目視し、料理、皿、敷物が写ることを確認しました。顔、人物、氏名、位置情報にあたるものは見つかりませんでした。全JPEGを調べ、GPS・EXIF・orientationメタデータはありませんでした。固定版の作者・CC BY表示・データ提供論文を照合し、CC BY 4.0の帰属・変更表示を付して再配布する派生物として扱います。

## 利用上の制約

食事と撮影条件はインドネシアの研究・病院食環境に由来し、日本の学校給食を代表しません。家庭や学校の食べ残しを調べる課題では、地元の献立・実測値と比較してください。画像や推定結果を健康・栄養・患者個人の判断や医療用途に使わないでください。元データ作成者の推奨・承認を示すものではありません。
