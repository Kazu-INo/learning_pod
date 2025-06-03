# Claude自動化ワークフロー セットアップガイド

このガイドでは、LearnPodプロジェクトにClaude自動化ワークフローを導入する手順を説明します。

## 📋 前提条件

- GitHubリポジトリの管理者権限
- AnthropicのAPIキー
- GitHub CLI (`gh`) のインストール

## 🚀 セットアップ手順

### 1. Secrets設定

以下のSecretsをGitHubリポジトリに設定してください：

#### 必須
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### オプション
```bash
SLACK_CI_CHANNEL=your_slack_webhook_url_here
```

**設定方法：**
1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. "New repository secret" をクリック
3. Name と Secret を入力して保存

### 2. ラベル作成

```bash
# スクリプトを実行（GitHub CLI が必要）
./scripts/setup-labels.sh
```

または手動で以下のラベルを作成：

| ラベル名 | 色 | 説明 |
|---------|----|----- |
| `auto-generated` | #006b75 | Claude AIによって自動生成されたPR/Issue |
| `claude-failed` | #d73a4a | Claude自動化が失敗した際に付与 |
| `ci-fix` | #0075ca | CI修復の自動PR |
| `documentation` | #0075ca | ドキュメント関連 |
| `urgent` | #d73a4a | 緊急対応が必要 |
| `ci-failure` | #d73a4a | CI失敗関連 |
| `release` | #7057ff | リリース関連 |

### 3. ブランチ保護設定

1. Settings → Branches
2. "Add rule" for `main` branch:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging

## 🔧 各ワークフローの詳細

### 1. PR自動レビュー (`claude-pr-review.yml`)

**動作条件：**
- PR作成・更新時
- `ANTHROPIC_API_KEY` が設定されている

**テスト方法：**
```bash
# Actions タブ → Claude PR Review → Run workflow
# 任意のPR番号を入力して手動実行
```

### 2. Issue自動実装 (`claude-issue-impl.yml`)

**動作条件：**
- Issueに `bug` または `enhancement` ラベルが付与された時

**テスト方法：**
1. 新しいIssueを作成
2. `bug` または `enhancement` ラベルを追加
3. 自動でPRが作成されることを確認

### 3. ドキュメント自動生成 (`claude-docs.yml`)

**動作条件：**
- PRがマージされた時

**テスト方法：**
1. テスト用PRを作成・マージ
2. ドキュメント生成PRが自動作成されることを確認

### 4. CI自動修復 (`claude-ci-fix.yml`)

**動作条件：**
- CI ワークフローが失敗した時

**設定項目：**
- 最大修復試行回数: 3回
- Slack通知: `SLACK_CI_CHANNEL` 設定時のみ

### 5. リリースノート自動生成 (`claude-release-notes.yml`)

**動作条件：**
- `v*` パターンのタグがpushされた時

**テスト方法：**
```bash
# テスト用タグを作成
git tag v0.1.0-test
git push origin v0.1.0-test
```

## 🐛 トラブルシューティング

### よくある問題

#### 1. Claude actionが動作しない
```
使用する Claude action のバージョンを確認：
- anthropics/claude-code-action@beta (推奨)
- anthropics/claude-code-base-action@beta (高度な操作用)
```

#### 2. ラベルが見つからないエラー
```bash
# ラベル作成スクリプトを実行
./scripts/setup-labels.sh
```

#### 3. 権限エラー
```yaml
# 各ワークフローに適切な permissions を設定済み
permissions:
  contents: write
  pull-requests: write
  issues: write
```

#### 4. API制限エラー
- `max_tokens` 設定で使用量を制限
- 並行実行数を `concurrency` で制御

### ログ確認方法

1. Actions タブでワークフロー実行を確認
2. 各ステップのログを詳細表示
3. Claude actionの出力を確認

## 📊 監視とメンテナンス

### コスト監視
- Anthropic APIの使用量を定期的に確認
- `max_tokens` と `max_calls` で制限設定

### 品質監視
- 自動生成されたPRの品質を人間がレビュー
- 失敗パターンを分析して改善

### 定期メンテナンス
- Claude actionのバージョン更新
- ワークフロー設定の最適化
- 不要な `ci-fix/` ブランチの削除

## 🔒 セキュリティ考慮事項

### Secrets管理
- APIキーの定期ローテーション
- 最小権限の原則を適用

### コード安全性
- 自動生成コードの必須レビュー
- `auto-generated` ラベル付きPRは人間承認必須

### 外部PR対策
- `pull_request_target` の適切な使用
- Fork からのPRに対する制限

## 📈 効果測定

### 測定項目
- PR レビュー時間の短縮
- Issue 解決速度の向上
- ドキュメント更新率の向上
- CI 修復成功率

### 改善指標
- Claude生成コードの採用率
- 手動修正が必要な頻度
- 開発者満足度

---

このセットアップガイドに従って、段階的にClaude自動化を導入し、開発効率の向上を実現してください。 