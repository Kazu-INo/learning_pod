# Claude AI アシスタント ガイドライン

## コーディング規約

### Python
- ruffのルールに従う
- importは必ず一番上に書く
- 型ヒントを可能な限り使用する
- docstringはGoogle形式で記述する
- 変数名・関数名は日本語コメントを含めてわかりやすく命名する

### JavaScript/TypeScript
- ESLintとPrettierのルールに従う
- constを優先し、letは必要な場合のみ使用
- 非同期処理はasync/awaitを使用

### 共通
- コミットメッセージは「feat:」「fix:」「docs:」等のプレフィックスを使用
- 新機能は必ずテストを追加
- 既存のテストが失敗しないことを確認

## ディレクトリ構成

```
.
├── .github/
│   └── workflows/     # GitHub Actions ワークフロー
├── src/              # ソースコード
├── docs/             # ドキュメンテーション
├── outputs/          # 出力ファイル
└── tests/            # テストファイル
```

## テスト要件

- 新機能追加時は必ずユニットテストを追加
- カバレッジは80%以上を維持
- 統合テストも重要な機能には必須

## PR作成時の注意点

- Draft PRで作成し、レビューが必要
- `auto-generated` ラベルが付いた自動生成PRは人間のレビューが必須
- 変更内容を明確に記述する

## Issue対応

- `bug` または `enhancement` ラベルが付いたIssueは自動実装対象
- 実装前に要件を明確化する
- 進捗はIssueで報告する 