"""Q&A生成モジュール"""

import re
from pathlib import Path
from typing import Tuple

import yaml

from learnpod.generator import LLMClient, PromptBuilder
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


def build_questions(
    script_path: Path,
    output_dir: Path,
    total_questions: int = 20,
    ratios: Tuple[float, float, float] = (0.5, 0.4, 0.1),
) -> Tuple[Path, Path]:
    """
    Q&Aセットとフラッシュカードを生成
    
    Args:
        script_path: 台本ファイルのパス
        output_dir: 出力ディレクトリ
        total_questions: 総問題数
        ratios: (Keyword, Why, Open)の比率
        
    Returns:
        (Q&Aファイルのパス, フラッシュカードファイルのパス)
    """
    logger.info(f"Q&A生成開始: {script_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 台本の読み込み
    script_content = script_path.read_text(encoding="utf-8")
    
    # LLMクライアントの初期化
    llm_client = LLMClient()
    
    # Q&Aプロンプトの生成
    qa_prompt = PromptBuilder.build_qa_prompt(
        content=script_content,
        total_questions=total_questions,
        ratios=ratios,
    )
    
    # Q&Aの生成
    qa_content = llm_client.generate(qa_prompt, temperature=0.6)
    
    # Q&Aの後処理
    qa_content = _post_process_qa(qa_content)
    
    # Q&Aファイルの保存
    qa_path = output_dir / "questions.md"
    qa_path.write_text(qa_content, encoding="utf-8")
    
    # Keyword Q&Aの抽出
    keyword_qa = _extract_keyword_qa(qa_content)
    
    # フラッシュカードYAMLの生成
    flashcard_path = None
    if keyword_qa:
        flashcard_path = _generate_flashcard_yaml(
            keyword_qa, output_dir, llm_client
        )
    
    logger.info(f"Q&A生成完了: {qa_path}")
    if flashcard_path:
        logger.info(f"フラッシュカード生成完了: {flashcard_path}")
    
    return qa_path, flashcard_path


def _post_process_qa(qa_content: str) -> str:
    """
    Q&Aの後処理
    
    Args:
        qa_content: 生成されたQ&A内容
        
    Returns:
        後処理済みのQ&A
    """
    # ヘッダーの追加
    header = f"""# Q&Aセット

このドキュメントは、ポッドキャスト内容の理解度を確認するためのQ&Aセットです。
各問題には回答が付いているので、自己採点に活用してください。

---

"""
    
    # 内容の整形
    qa_content = qa_content.strip()
    
    # マークダウンコードブロックの除去
    qa_content = re.sub(r'```markdown\n?', '', qa_content)
    qa_content = re.sub(r'```\n?', '', qa_content)
    
    # 問題番号の整形
    qa_content = re.sub(r'\*\*Q(\d+):\*\*', r'**Q\1:**', qa_content)
    qa_content = re.sub(r'\*\*A:\*\*', r'**A:**', qa_content)
    
    # 空行の整理
    qa_content = re.sub(r'\n{3,}', '\n\n', qa_content)
    
    return header + qa_content


def _extract_keyword_qa(qa_content: str) -> str:
    """
    Keyword Q&Aセクションを抽出
    
    Args:
        qa_content: Q&A内容
        
    Returns:
        Keyword Q&Aセクション
    """
    # Keyword Q&Aセクションの抽出
    keyword_match = re.search(
        r'## Keyword Q&A\s*\n(.*?)(?=## |$)',
        qa_content,
        re.DOTALL
    )
    
    if keyword_match:
        return keyword_match.group(1).strip()
    
    logger.warning("Keyword Q&Aセクションが見つかりませんでした")
    return ""


def _generate_flashcard_yaml(
    keyword_qa: str, output_dir: Path, llm_client: LLMClient
) -> Path:
    """
    フラッシュカードYAMLを生成
    
    Args:
        keyword_qa: Keyword Q&Aセクション
        output_dir: 出力ディレクトリ
        llm_client: LLMクライアント
        
    Returns:
        フラッシュカードファイルのパス
    """
    # フラッシュカードプロンプトの生成
    flashcard_prompt = PromptBuilder.build_flashcard_yaml_prompt(keyword_qa)
    
    # フラッシュカードYAMLの生成
    yaml_content = llm_client.generate(flashcard_prompt, temperature=0.3)
    
    # YAMLの後処理
    yaml_content = _post_process_yaml(yaml_content)
    
    # ファイル保存
    flashcard_path = output_dir / "flashcards.yaml"
    flashcard_path.write_text(yaml_content, encoding="utf-8")
    
    # YAML形式の検証
    try:
        yaml.safe_load(yaml_content)
        logger.debug("フラッシュカードYAMLの形式検証成功")
    except yaml.YAMLError as e:
        logger.warning(f"フラッシュカードYAMLの形式に問題があります: {e}")
        # 手動でフラッシュカードを生成
        yaml_content = _generate_fallback_yaml(keyword_qa)
        flashcard_path.write_text(yaml_content, encoding="utf-8")
    
    return flashcard_path


def _post_process_yaml(yaml_content: str) -> str:
    """
    YAMLの後処理
    
    Args:
        yaml_content: 生成されたYAML内容
        
    Returns:
        後処理済みのYAML
    """
    # YAMLコードブロックの除去
    yaml_content = re.sub(r'```yaml\n?', '', yaml_content)
    yaml_content = re.sub(r'```\n?', '', yaml_content)
    
    # 不要な説明文の除去
    lines = yaml_content.split('\n')
    yaml_lines = []
    in_yaml = False
    
    for line in lines:
        if line.strip().startswith('flashcards:'):
            in_yaml = True
        
        if in_yaml:
            yaml_lines.append(line)
    
    return '\n'.join(yaml_lines).strip()


def _generate_fallback_yaml(keyword_qa: str) -> str:
    """
    フォールバック用のフラッシュカードYAMLを生成
    
    Args:
        keyword_qa: Keyword Q&Aセクション
        
    Returns:
        フラッシュカードYAML
    """
    flashcards = []
    
    # Q&Aの解析
    qa_pattern = r'\*\*Q\d+:\*\*\s*(.+?)\s*\*\*A:\*\*\s*(.+?)(?=\*\*Q\d+:|$)'
    matches = re.findall(qa_pattern, keyword_qa, re.DOTALL)
    
    for i, (question, answer) in enumerate(matches):
        question = question.strip()
        answer = answer.strip()
        
        # flashcard IDコメントを除去
        answer = re.sub(r'<!--.*?-->', '', answer).strip()
        
        flashcard = {
            'id': f'keyword_{i+1:02d}',
            'front': question,
            'back': answer,
            'category': 'keyword'
        }
        flashcards.append(flashcard)
    
    yaml_data = {'flashcards': flashcards}
    return yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False) 