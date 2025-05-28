"""プロンプト生成モジュール"""

from typing import Dict, List, Tuple


class PromptBuilder:
    """プロンプト生成クラス"""
    
    @staticmethod
    def build_script_prompt(
        content: str,
        language: str = "ja",
        target_length: int = 20,
        speakers: Dict[str, str] = None,
    ) -> str:
        """
        台本生成プロンプトを構築
        
        Args:
            content: 入力コンテンツ
            language: 言語設定
            target_length: 目標時間（分）
            speakers: スピーカー設定
            
        Returns:
            台本生成プロンプト
        """
        if speakers is None:
            speakers = {"S1": "Sakura", "S2": "Taro"}
        
        speaker_list = "\n".join([f"- {k}: {v}" for k, v in speakers.items()])
        
        return f"""あなたは教育的なポッドキャスト台本の専門家です。以下の学習資料を基に、{target_length}分程度のポッドキャスト台本を作成してください。

## 入力資料
{content}

## 要件
- 言語: {language}
- 目標時間: {target_length}分（約{target_length * 150}語）
- スピーカー構成:
{speaker_list}

## 台本作成ガイドライン
1. **わかりやすさ最優先**: 専門用語は必ず説明を加える
2. **対話形式**: 自然な会話で進行し、聞き手の理解を促進
3. **構造化**: 導入→本論→まとめの流れを明確に
4. **具体例**: 抽象的な概念には実例を交える
5. **学習促進**: 重要ポイントは繰り返しや言い換えで強調

## 出力フォーマット
各発言は以下の形式で記述してください：

Speaker 1: [発言内容]
Speaker 2: [発言内容]

## 注意事項
- 各スピーカーの発言は自然で、教育的価値の高い内容にする
- 聞き手が理解しやすいペースで情報を提示する
- 専門用語や概念は必ず解説を含める
- 実用的な応用例や背景情報も適切に織り込む

台本を作成してください："""

    @staticmethod
    def build_explainer_prompt(script_content: str) -> str:
        """
        詳細解説生成プロンプトを構築
        
        Args:
            script_content: 台本内容
            
        Returns:
            詳細解説生成プロンプト
        """
        return f"""あなたは教育コンテンツの解説専門家です。以下のポッドキャスト台本を基に、詳細解説を作成してください。

## 台本内容
{script_content}

## 解説作成ガイドライン
1. **曖昧な部分の具体化**: 台本で省略された概念や背景を詳しく説明
2. **根拠の提示**: 主張や理論の根拠、出典、関連研究を明記
3. **実用例の追加**: 理論を実際の場面でどう活用するかを示す
4. **段階的理解**: 基礎から応用まで段階的に理解を深める構成
5. **読みやすさ**: 「読みながら理解を促す」語り口で記述

## 出力フォーマット
台本の各セクションに対して以下の形式で解説を作成：

### [セクション名]

> [台本からの引用]

#### 詳細解説
[具体的な解説内容]

#### 背景・根拠
[理論的背景や根拠となる情報]

#### 実用例
[実際の応用例や具体的なケース]

## 注意事項
- 台本の内容を補完し、より深い理解を促進する
- 専門用語は必ず定義と説明を含める
- 文献や参考資料があれば適切に言及する
- 読者が段階的に理解できるよう配慮する

詳細解説を作成してください："""

    @staticmethod
    def build_qa_prompt(
        content: str,
        total_questions: int = 20,
        ratios: Tuple[float, float, float] = (0.5, 0.4, 0.1),
    ) -> str:
        """
        Q&A生成プロンプトを構築
        
        Args:
            content: 対象コンテンツ
            total_questions: 総問題数
            ratios: (Keyword, Why, Open)の比率
            
        Returns:
            Q&A生成プロンプト
        """
        keyword_count = int(total_questions * ratios[0])
        why_count = int(total_questions * ratios[1])
        open_count = total_questions - keyword_count - why_count
        
        return f"""あなたは教育的なQ&A作成の専門家です。以下のコンテンツを基に、学習効果の高いQ&Aセットを作成してください。

## 対象コンテンツ
{content}

## Q&A作成要件
- 総問題数: {total_questions}問
- Keyword Q&A: {keyword_count}問（50%）- 重要な用語や概念の定義
- Why Q&A: {why_count}問（40%）- 理由や原因を問う問題
- Open Questions: {open_count}問（10%）- 応用や考察を促す問題

## 各カテゴリの特徴
### Keyword Q&A
- 重要な用語、概念、定義を問う
- 明確で簡潔な答えがある
- フラッシュカード学習に適している

### Why Q&A
- 「なぜ」「どうして」を問う
- 理由、原因、メカニズムを説明させる
- 理解の深さを確認する

### Open Questions
- 応用、考察、批判的思考を促す
- 複数の答えが考えられる
- 創造的思考を刺激する

## 出力フォーマット
```markdown
## Keyword Q&A
- **Q1:** [問題文]  
  **A:** [回答]  <!-- flashcard:id=[英数字のID] -->

- **Q2:** [問題文]  
  **A:** [回答]  <!-- flashcard:id=[英数字のID] -->

## Why Q&A
- **Q{keyword_count + 1}:** [問題文]  
  **A:** [回答]

## Open Questions
- **Q{keyword_count + why_count + 1}:** [問題文]  
  **A:** [回答例や考察のポイント]
```

## 注意事項
- 各問題には必ず回答を付ける（自己採点用）
- Keyword問題にはflashcard用のIDコメントを追加
- 問題の難易度は段階的に設定
- 実用的で学習効果の高い内容にする

Q&Aセットを作成してください："""

    @staticmethod
    def build_flashcard_yaml_prompt(keyword_qa: str) -> str:
        """
        フラッシュカードYAML生成プロンプトを構築
        
        Args:
            keyword_qa: Keyword Q&Aセクション
            
        Returns:
            フラッシュカードYAML生成プロンプト
        """
        return f"""以下のKeyword Q&Aを基に、フラッシュカード学習用のYAMLファイルを作成してください。

## Keyword Q&A
{keyword_qa}

## 出力フォーマット
```yaml
flashcards:
  - id: [flashcard:idから抽出したID]
    front: "[問題文]"
    back: "[回答]"
    category: "keyword"
    
  - id: [次のID]
    front: "[問題文]"
    back: "[回答]"
    category: "keyword"
```

## 注意事項
- IDは英数字のみ使用
- frontは問題文、backは回答
- categoryは"keyword"で統一
- YAML形式を正確に守る

フラッシュカードYAMLを作成してください：""" 