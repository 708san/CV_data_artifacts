# Artifact manifest

各artifactには、`manifest-v1.schema.json`に適合するmanifestを添付します。manifestは、データ本体の代わりに、公開するファイルの相対パス・サイズ・SHA-256、画像数、ラベル形式、変換版、ライセンス、出典を記録する台帳です。

manifestの`source.sha256`は、元データの固定アーカイブまたは固定ファイル集合を表します。元データに単一の固定アーカイブがない場合は、公開artifactを作成する前に、固定方法を別途決めてください。動的な`main`や`latest`だけを参照するmanifestは受け付けません。

公開前には、次を確認します。

1. `files`の全対象ファイルを実際に取得し、記載のSHA-256とサイズを照合する。
2. パスがartifactルート外へ出ないこと、シンボリックリンクを含まないことを確認する。
3. 画像とラベルの件数・対応・分割・重複を検査する。
4. ライセンス、元画像の権利、改変・再配布・教材公開の範囲を分けて記録する。
5. `registry/datasets.json`のartifact URL、manifest URL、監査レポートURL、SHA-256を一致させる。
