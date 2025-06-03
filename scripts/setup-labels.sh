#!/bin/bash

# GitHub リポジトリラベル設定スクリプト
# Claude自動化ワークフローで使用されるラベルを作成

set -e

echo "🏷️  GitHubラベルを設定中..."

# 基本的なラベル（既存の場合は更新）
gh label create "auto-generated" --description "Claude AIによって自動生成されたPR/Issue" --color "006b75" --force
gh label create "claude-failed" --description "Claude自動化が失敗した際に付与" --color "d73a4a" --force
gh label create "ci-fix" --description "CI修復の自動PR" --color "0075ca" --force
gh label create "documentation" --description "ドキュメント関連" --color "0075ca" --force

# 重要度ラベル
gh label create "urgent" --description "緊急対応が必要" --color "d73a4a" --force
gh label create "high-priority" --description "高優先度" --color "ff9500" --force
gh label create "medium-priority" --description "中優先度" --color "fbca04" --force
gh label create "low-priority" --description "低優先度" --color "0e8a16" --force

# 種類別ラベル
gh label create "ci-failure" --description "CI失敗関連" --color "d73a4a" --force
gh label create "release" --description "リリース関連" --color "7057ff" --force

echo "✅ ラベル設定完了！"
echo ""
echo "作成されたラベル:"
gh label list 