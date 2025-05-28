"""詳細解説生成モジュール"""

from pathlib import Path

from learnpod.generator import LLMClient, PromptBuilder
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


def build_explainer(script_path: Path, output_dir: Path) -> Path:
    """
    詳細解説を生成
    
    Args:
        script_path: 台本ファイルのパス
        output_dir: 出力ディレクトリ
        
    Returns:
        生成された詳細解説ファイルのパス
    """
    logger.info(f"詳細解説生成開始: {script_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 台本の読み込み
    script_content = script_path.read_text(encoding="utf-8")
    
    # LLMクライアントの初期化
    llm_client = LLMClient()
    
    # プロンプトの生成
    prompt = PromptBuilder.build_explainer_prompt(script_content)
    
    # 詳細解説の生成
    explanation = llm_client.generate(prompt, temperature=0.5)
    
    # 解説の後処理
    explanation = _post_process_explanation(explanation, script_content)
    
    # ファイル保存
    explainer_path = output_dir / "explanation.md"
    explainer_path.write_text(explanation, encoding="utf-8")
    
    logger.info(f"詳細解説生成完了: {explainer_path}")
    return explainer_path


def _post_process_explanation(explanation: str, script_content: str) -> str:
    """
    詳細解説の後処理
    
    Args:
        explanation: 生成された詳細解説
        script_content: 台本内容
        
    Returns:
        後処理済みの詳細解説
    """
    # ヘッダーの追加
    header = f"""# 詳細解説

このドキュメントは、ポッドキャスト台本の内容をより深く理解するための詳細解説です。
台本で触れられた概念や理論について、背景・根拠・実用例を含めて詳しく説明します。

---

"""
    
    # 解説内容の整形
    explanation = explanation.strip()
    
    # 不適切な見出しレベルの修正
    import re
    
    # H1見出しをH2に変更（ドキュメント全体のH1は上記のヘッダーのみ）
    explanation = re.sub(r'^# ', '## ', explanation, flags=re.MULTILINE)
    
    # 引用ブロックの整形
    explanation = re.sub(r'^>\s*(.+)$', r'> \1', explanation, flags=re.MULTILINE)
    
    # 空行の整理
    explanation = re.sub(r'\n{3,}', '\n\n', explanation)
    
    return header + explanation 