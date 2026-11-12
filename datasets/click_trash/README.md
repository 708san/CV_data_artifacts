# CLICK Trash v0.1.0

物体検出用の画像1,126枚と、ごみの位置を示すYOLO形式の枠注釈2,213件です。クラスは`trash`の1種類です。4枚はごみが写っていない画像で、空のラベルを保っています。

## 使える課題

学校や地域の清掃活動で、道や草地に落ちているごみを見つけて記録する試作に使えます。元画像はインドの屋外環境で撮影されているため、日本の通学路の代表データではありません。地域で使う場合は、生徒が撮影した画像でも動作を確かめてください。検出結果は清掃記録づくりを補助するもので、分別方法や危険性を判定しません。

## 収録内容

- train 901枚、valid 113枚、test 112枚
- 画像は長辺最大1,024pxのJPEG
- `labels/`には1画像ごとのYOLO正規化bboxを収録
- `annotations.jsonl`には画像・split・bboxの共通形式を収録
- `metadata.jsonl`には画像ごとの注釈件数を収録
- 元データのsingle-classラベルだけを使用。クラス数に偏りのある13クラス版とポリゴン注釈は含めていません

## 変換

画像を長辺最大1,024px、JPEG品質0.88で書き出し、元画像のEXIF・GPS・カメラ情報を除きました。元からorientation値はすべて標準向きでした。画像の縮小後も、正規化されたbbox座標は変更していません。元のtrain/val/test分割を維持し、`val`を共通形式の`valid`へ名称変更しました。

## 出典・ライセンス

Manjit Baishya (2026), [CLICK Trash Dataset, Mendeley Data v2](https://data.mendeley.com/datasets/htcvvz6fm2/2), DOI [10.17632/htcvvz6fm2.2](https://doi.org/10.17632/htcvvz6fm2.2), CC BY 4.0. 出典表示と変更内容は同梱の`LICENSE.md`を参照してください。
