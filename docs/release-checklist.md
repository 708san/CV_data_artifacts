# Release checklist

データartifactのGitHub Releaseを作成する前に、次をすべて満たします。

- [ ] 元データの公式URL、固定版、固定SHA-256がある
- [ ] ライセンス本文と元画像の権利を確認し、改変・再配布・教材公開の範囲を記録した
- [ ] 変換スクリプトと変換版を保存した
- [ ] manifestの全ファイルを実測し、SHA-256・サイズ・画像数・ラベル対応を確認した
- [ ] パストラバーサル、シンボリックリンク、重複ファイルを検査した
- [ ] 監査レポートを保存した
- [ ] `registry/datasets.json`が`approved_for_redistribution`になっている
- [ ] CV_data側の課題APIとデータ別説明が、実際に公開したartifactだけを案内している
- [ ] Git履歴にraw dataや秘密情報を入れていない

どれか一つでも未完了なら、Release assetやPyPIから利用可能と案内しません。
