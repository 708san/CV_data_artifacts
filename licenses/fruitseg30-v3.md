# FruitSeg30 v3 — 利用条件・出典

## 固定版とライセンス表示

- 公式データ：[Mendeley Data v3](https://data.mendeley.com/datasets/vkht8pfsp3/3)、DOI `10.17632/vkht8pfsp3.3`
- ライセンス表示：Mendeley Dataのv3ページにCC BY 4.0と表示。関連データ論文もCC BYで公開。
- 公式ページは30クラス、画像1,969枚とマスク1,969枚、各512×512と説明。論文は著者らがマレーシア、バングラデシュ、オーストラリアの複数地点で果物画像を撮影・収集したと説明。
- 全3,938ファイルを公式の固定ファイルID・サイズ・SHA-256と照合した。各ファイルの情報は`manifests/sources/fruitseg30-v3.json`に記録。

## 帰属表示

> F. M. Javed Mehedi Shamrat; Rashiduzzaman Shakil; Mohd Yamani Idna Idris; Bonna Akter; Xujuan Zhou (2024), “FruitSeg30_Segmentation Dataset & Mask Annotations,” Mendeley Data v3, DOI: 10.17632/vkht8pfsp3.3, CC BY 4.0.

## 変更内容

教材用artifact v0.1.0ではGuavaクラス55画像・55マスクを除外。残り29クラス1,914組は画像とマスクの画素を変更せず保持し、クラス内seed 42でtrain/val/testへ分割した。分割表、除外理由、ファイル単位のSHA-256はartifact manifestと監査reportに記録。

## 権利・利用上の留保

公式ページのCC BY 4.0表示とデータ論文の撮影説明を確認した。公式記録内に別の競合ライセンス表示は見当たらなかった。全画像の第三者権利や撮影参加者の有無を独立に目視確認したわけではないため、これを権利の無制限な保証とは扱わない。

このデータは果物領域の画像分割演習向けで、鮮度・品質・食品安全の判定には使わない。Mendeley v3とCC BY 4.0の帰属表示をartifactと教材に残す。
