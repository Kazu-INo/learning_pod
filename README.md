# LearnPod

個人の学習・研究アウトプット（Markdown形式）から、ポッドキャスト音声とQ&Aセットを自動生成するシステムです。

## 🎯 概要

LearnPodは、あなたの学習ノートや研究資料を以下のコンテンツに自動変換します：

- 🎧 **ポッドキャスト音声**（15-20分、マルチスピーカー）
- 📝 **台本 + 詳細解説テキスト**
- ❓ **Q&Aセット**（自己採点＋フラッシュカード化可能）
- 📧 **Gmail自動配信**（上記一式をメールで送信）

## 🚀 特徴

- **最新のGemini API**を使用（`google-genai` 1.16.1+）
- **マルチスピーカーTTS**による自然な対話形式
- **学習効果重視**：わかりやすさ最優先、専門用語は必ず説明
- **Docker対応**：環境構築が簡単
- **CLI操作**：シンプルなコマンドで実行

## 📋 必要な環境

- Python 3.10+
- Docker（推奨）
- Gemini API キー
- Gmail アカウント（メール送信用、オプション）

## 🛠️ インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-repo/learnpod.git
cd learnpod
```

### 2. 環境変数の設定

テンプレートファイルをコピーして設定：

```bash
# テンプレートファイルをコピー
cp env.template .env

# .envファイルを編集して実際の値を設定
# 必須: GEMINI_API_KEY
# オプション: Gmail設定（GMAIL_USER, GMAIL_PASSWORD, GMAIL_TO）
```

`.env`ファイルの例：

```bash
# 必須
GEMINI_API_KEY=your_actual_api_key_here

# オプション（メール送信用）
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD=your_app_password
GMAIL_TO=recipient@gmail.com
```

**重要**: 
- Gemini API キーは [Google AI Studio](https://aistudio.google.com/app/apikey) から取得してください
- Gmail App Passwordの設定方法は [こちら](https://support.google.com/accounts/answer/185833) を参照

### 3. Dockerを使用した実行（推奨）

```bash
# イメージのビルド
docker build -t learnpod .

# 実行
docker run -v $(pwd)/outputs:/app/outputs --env-file .env learnpod run input.md
```

### 4. ローカル環境での実行

```bash
# 依存関係のインストール
pip install -e .

# 実行
learnpod run input.md
```

## 📖 使用方法

### 基本的な使用方法

```bash
# フルパイプライン実行
learnpod run your_notes.md

# オプション付き実行
learnpod run your_notes.md --length 15 --lang ja --no-email
```

### 個別ステップの実行

```bash
# 1. ファイル内容の確認
learnpod ingest your_notes.md

# 2. 台本のみ生成
learnpod script your_notes.md --length 20

# 3. 音声のみ生成（台本から）
learnpod audio script.md --voices "Speaker 1=Zephyr,Speaker 2=Puck"

# 4. Q&Aのみ生成（台本から）
learnpod questions script.md

# 5. 設定確認
learnpod config-check
```

### コマンドオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--length` | 音声の長さ（分） | 20 |
| `--lang` | 言語設定 | ja |
| `--speakers` | スピーカー設定 | Speaker 1=Sakura,Speaker 2=Taro |
| `--voices` | 音声設定 | Speaker 1=Zephyr,Speaker 2=Puck |
| `--no-email` | メール送信をスキップ | False |

## 📁 入力ファイル形式

### Markdownファイル

```markdown
---
title: "機械学習の基礎"
author: "あなたの名前"
date: "2024-01-15"
---

# 機械学習とは

機械学習は、コンピュータがデータから自動的に学習し...

## 教師あり学習

教師あり学習では、入力と正解のペアを使って...

### 線形回帰

線形回帰は最もシンプルな機械学習手法の一つで...
```

### YAML Front-Matter（オプション）

- `title`: ポッドキャストのタイトル
- `author`: 著者名
- `date`: 作成日
- その他のメタデータ

## 📤 出力ファイル

実行後、`outputs/YYMMDD_HHMM/`ディレクトリに以下が生成されます：

```
outputs/250115_1430/
├── input_your_notes.md      # 入力ファイルのコピー
├── script.md                # ポッドキャスト台本
├── explanation.md           # 詳細解説
├── questions.md             # Q&Aセット
├── flashcards.yaml          # フラッシュカード
└── podcast.mp3              # 音声ファイル
```

## 🎵 音声設定

### 利用可能な音声

Gemini TTSで利用可能な音声：
- **Zephyr**: 男性、落ち着いた声
- **Puck**: 女性、明るい声
- **Sakura**: 女性、やわらかい声
- **Taro**: 男性、はっきりした声

### スピーカー設定例

```bash
# 2人の対話
--speakers "Speaker 1=Sakura,Speaker 2=Taro" --voices "Speaker 1=Zephyr,Speaker 2=Puck"

# 3人の対話
--speakers "Speaker 1=Host,Speaker 2=Expert,Speaker 3=Student" --voices "Speaker 1=Zephyr,Speaker 2=Puck,Speaker 3=Sakura"
```

## 📧 メール送信機能

Gmail設定が完了している場合、生成されたコンテンツが自動的にメールで送信されます：

- 📎 **添付ファイル**: 音声、台本、解説、Q&A、フラッシュカード
- 📊 **詳細情報**: ファイルサイズ、音声時間、問題数など
- 🔒 **セキュア**: Gmail App Passwordを使用

## 🐳 Docker設定

### Dockerfile

```dockerfile
FROM python:3.11-slim

# システム依存関係
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY pyproject.toml .
RUN pip install uv && uv pip install --system .

# アプリケーション
COPY src/ /app/src/
WORKDIR /app

ENTRYPOINT ["learnpod"]
```

### docker-compose.yml（例）

```yaml
version: '3.8'
services:
  learnpod:
    build: .
    volumes:
      - ./inputs:/app/inputs
      - ./outputs:/app/outputs
    env_file:
      - .env
    command: run /app/inputs/your_notes.md
```

## 🔧 設定

### config.py

主要な設定項目：

```python
# モデル設定
llm_model = "gemini-2.5-pro-preview-05-06"
tts_model = "gemini-2.5-flash-preview-tts"

# 音声設定
chunk_size = 800  # トークン数
target_words = (2000, 3000)  # 台本の目標語数

# デフォルト設定
default_language = "ja"
default_length = 20
```

## 🧪 開発

### 開発環境のセットアップ

```bash
# 開発依存関係のインストール
pip install -e ".[dev]"

# コード品質チェック
ruff check src/
black src/
mypy src/

# テスト実行
pytest tests/
```

### プロジェクト構造

```
learning_pod/
├── src/learnpod/
│   ├── cli.py              # CLIインターフェース
│   ├── config.py           # 設定管理
│   ├── generator/          # LLM・TTS生成
│   ├── pipeline/           # パイプライン処理
│   ├── email/              # メール送信
│   └── utils/              # ユーティリティ
├── outputs/                # 出力ディレクトリ
├── pyproject.toml          # プロジェクト設定
├── Dockerfile              # Docker設定
└── README.md               # このファイル
```

## 🤝 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 🙏 謝辞

- [Google Gemini API](https://ai.google.dev/gemini-api/docs/libraries?hl=ja) - 最新のLLM・TTS技術
- [pydub](https://github.com/jiaaro/pydub) - 音声処理
- [Click](https://click.palletsprojects.com/) - CLIフレームワーク

## 📞 サポート

- 🐛 **バグ報告**: [Issues](https://github.com/your-repo/learnpod/issues)
- 💡 **機能要望**: [Discussions](https://github.com/your-repo/learnpod/discussions)
- 📧 **お問い合わせ**: team@learnpod.dev

---

**LearnPod v0.2.0** - あなたの学習を次のレベルへ 🚀