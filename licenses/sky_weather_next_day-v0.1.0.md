# 空画像と翌日の天気：権利・利用条件

## データと出典

**空画像**：Joshua E. Hammond、Brian A. Korgel、NREL SRRL Minute-Resolution Sky Imagery Dataset。取得元のデータセットカードはCC BY 4.0を表示しています。  
https://huggingface.co/datasets/knl2366/NREL_Sky_Imagery

**気象データ**：Open-Meteo Historical Weather APIのERA5再解析値。Open-MeteoはデータをCC BY 4.0で提供しています。  
https://open-meteo.com/en/docs/historical-weather-api  
https://open-meteo.com/en/license

**ライセンス**：Creative Commons Attribution 4.0 International (CC BY 4.0)  
https://creativecommons.org/licenses/by/4.0/

## 利用時の表示

再配布・改変時は上記出典を表示し、CC BY 4.0へのリンクを含め、変更を明示してください。推奨表示：

> Joshua E. Hammond and Brian A. Korgel, NREL SRRL Minute-Resolution Sky Imagery Dataset; weather values from Open-Meteo Historical Weather API (ERA5). Modified for CV education: normalized file layout and indexes; source JPEG pixels preserved; next-day labels and chronological split retained. CC BY 4.0.

Open-Meteoの**無料APIサービス利用条件**は非商用です。教育コンテンツでの利用は同サービスの条件に例示されています。このサービス条件は、CC BY 4.0というデータライセンスとは別です。データ利用者がAPIから新たにデータを取得する場合は、その時点の最新条件を確認してください。

## 変更内容

- 入力：ユーザー提供の `sky-weather-next-day.zip`（10,014,296 bytes、SHA-256 `c30cf675819fea9b0bad62e0d0c8cb77890b808253e92c604b39d6c97a6f5280`）。
- 画像1,000枚のJPEG画素データは変更せず、`images/<split>/<class>/`へ整理。
- 分類ラベル、固定MSTの日時、翌日降水量・降雪量・平均雲量などを`labels.csv`へ収録。標準索引とmanifestを追加。
- 教材用ルールによる翌日天気分類と、元の時系列splitを維持。
- 整形済みZIPのSHA-256：`c438ca3444bf72773d4a7bb430ed3f20885db8fbb0fd5d3f00ee7727149564e0`。

## 上流版の固定について

提供ZIPに画像データセットの完全な上流commit/revisionは記録されていません。そのため、上流の固定版を確認したとは扱いません。入力ZIPと整形済みZIPをSHA-256で固定しています。Open-Meteoの元APIレスポンスの個別ファイルも入力ZIP内にありません。

## 内容上の制限

- 画像はColorado州GoldenのNREL SRRL 1地点です。日本や他地域の空・天候を代表しません。
- 気象値はERA5再解析値であり、公式予報や現地の直接観測ではありません。
- 時刻表記のMSTは固定UTC−7で、夏時間を反映しません。
- train/validation/testのクラス比率には差があります。特にtestでrainyの割合が高く、単一の正解率だけでは性能を説明できません。
- このデータは、実際の外出・防災・農業などの判断に使うものではありません。
