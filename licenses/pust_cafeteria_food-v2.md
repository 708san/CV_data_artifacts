# PUST Cafeteria Food Image Dataset v2 — 利用条件記録

- 出典: [Mendeley Data v2](https://data.mendeley.com/datasets/fn6yhzjz83/2)
- DOI: `10.17632/fn6yhzjz83.2`
- 提供者: Marufa Yeasmin、Md. Razu Ahmed、Protiva Rani Kundu、Jannatul Mauya、Md. Shamim Reza
- ライセンス: CC BY 4.0（公式記録）
- 利用判断: 高校生向けの食堂・料理画像認識の試作に使える。日本の食堂を代表しない。栄養・価格・アレルギー・衛生・食べ残しの判断には使わない。

## 取得・整形

使用ファイルは`02_processed_data.zip`（file ID `9e24b022-b800-45bb-b5fb-1f6d0169db9f`、SHA-256 `f2f85952807a2d64d50b958c9355829cb5cad8636d611b2b9d7357e7267250a1`）と、対応表等を含む`03_metadata.zip`（file ID `f17ac06f-e635-43bd-b063-072f309cf51b`、SHA-256 `5e93b20b4e2e2d2844028d9e0dcc200ecaddecbbad0d943a6f4dedf930f6a73e`）です。両ファイルのサイズとSHA-256を照合後に安全に展開しました。加工済みデータの対応表からaugmentation_statusがoriginalの画像のみ選び、拡張画像を除外。ファイル名に`removebg`を含む29画像を除き、691枚を収録しています。

画像画素は変更せず、元画像単位のtrain/validation/test分割を維持しました。polygon 2,510件は軸平行bboxへ変換。561注釈に含まれる境界外座標904個を画像範囲にクリップしました。変換により輪郭形状は失われます。

## 権利・教材上の注意

食器・包装のロゴや部分的な手が写る画像があります。顔を確認した画像はありませんでした。第三者ロゴの権利や推奨をこのデータライセンスが別途許諾するものとは扱いません。ライブラリ配布前の候補であり、固定Release assetへの公開後にのみ利用可能として登録します。
