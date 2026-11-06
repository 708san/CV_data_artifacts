# 固定source manifest

ここには、元データをRelease assetとして公開したものではなく、公式配布元から再取得するためのファイル単位inventoryを保存します。

各項目は、提供元の固定版、ファイルID、ファイル名、サイズ、SHA-256、取得URLを記録します。Mendeley Dataのように単一アーカイブSHA-256がない場合でも、ファイル集合と各ファイルのハッシュを固定して、取得後に検証できます。

このinventoryだけでは、教材利用・改変・再配布の許可を意味しません。`registry/datasets.json`に登録されていないsource manifestは、正式APIや公開Releaseから利用可能とは案内しません。
