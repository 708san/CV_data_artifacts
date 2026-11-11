# Fashion-MNIST v0.1 — 出典・利用条件

- 出典：[Zalando Research公式リポジトリの固定コミット](https://github.com/zalandoresearch/fashion-mnist/tree/b2617bb6d3ffa2e429640350f613e3291e10b141)
- 固定コミット：`b2617bb6d3ffa2e429640350f613e3291e10b141`
- 作成者：Han Xiao、Kashif Rasul、Roland Vollgraf。画像提供：Zalando SE。
- ライセンス：公式READMEのLicense欄と同コミットのLICENSEファイルがMIT Licenseを掲示。著作権表示・許諾表示を含む全文を配布ZIPの`LICENSE.md`に収録。
- 帰属表示：Zalando SE (2017), Fashion-MNIST; Han Xiao, Kashif Rasul, and Roland Vollgraf, *Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms*; 固定コミットとMIT Licenseを表示する。

## 固定元ファイル

| ファイル | bytes | SHA-256 |
| --- | ---: | --- |
| `train-images-idx3-ubyte.gz` | 26,421,880 | `3aede38d61863908ad78613f6a32ed271626dd12800ba2636569512369268a84` |
| `train-labels-idx1-ubyte.gz` | 29,515 | `a04f17134ac03560a47e3764e11b92fc97de4d1bfaf8ba1a3aa29af54cc90845` |
| `t10k-images-idx3-ubyte.gz` | 4,422,102 | `346e55b948d973a97e58d2351dde16a484bd415d4595297633bb08f03db6a073` |
| `t10k-labels-idx1-ubyte.gz` | 5,148 | `67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5` |

4ファイルのサイズとSHA-256を検証してから展開しました。manifestの`source.sha256`は、ファイル名の昇順に各ファイル名・NUL byte・圧縮ファイル全bytesを連結したバイト列のSHA-256です。元ファイル個別の値は上表と監査レポートに記録しています。

## 変換と利用上の注意

IDXの各28×28 grayscale pixel値を変更せず、PGM P5へ格納形式だけ変換しました。元の60,000枚のtrainをクラスごとに決定的に分け、train 54,000枚、validation 6,000枚を作成。公式test 10,000枚は維持しました。

このデータは衣類画像分類のベンチマークです。小さな白黒商品画像であり、実際の衣類写真、状態、色、サイズ、ブランド、再利用可否を表しません。実環境の衣類整理へ適用できる性能を保証しません。商品画像内の意匠や商標に別個の権利が存在する可能性があり、ブランド識別や推奨の教材には使いません。
