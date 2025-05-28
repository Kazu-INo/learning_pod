"""台本生成モジュール"""

from pathlib import Path
from typing import Dict, Optional

from learnpod.generator import LLMClient, PromptBuilder, TextSplitter
from learnpod.pipeline.ingest import IngestedDoc
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


def build_script(
    doc: IngestedDoc,
    output_dir: Path,
    language: str = "ja",
    target_length: int = 20,
    speakers: Optional[Dict[str, str]] = None,
) -> Path:
    """
    台本を生成
    
    Args:
        doc: 取り込み済みドキュメント
        output_dir: 出力ディレクトリ
        language: 言語設定
        target_length: 目標時間（分）
        speakers: スピーカー設定
        
    Returns:
        生成された台本ファイルのパス
    """
    logger.info(f"台本生成開始: {doc.title}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # LLMクライアントの初期化
    llm_client = LLMClient()
    
    # コンテンツの準備
    content = doc.get_content_without_metadata()
    
    # トークン制限チェックと分割
    splitter = TextSplitter()
    if llm_client.is_token_limit_exceeded(content):
        logger.info("コンテンツが長すぎるため分割して処理します")
        chunks = splitter.split_by_tokens(content, llm_client)
        
        # 各チャンクで台本を生成して結合
        script_parts = []
        for i, chunk in enumerate(chunks):
            logger.info(f"チャンク {i+1}/{len(chunks)} の台本生成中...")
            
            prompt = PromptBuilder.build_script_prompt(
                content=chunk,
                language=language,
                target_length=target_length // len(chunks),  # 時間を分割
                speakers=speakers,
            )
            
            script_part = llm_client.generate(prompt, temperature=0.7)
            script_parts.append(script_part)
        
        # 台本の結合
        script = _merge_script_parts(script_parts)
    else:
        # 一括生成
        prompt = PromptBuilder.build_script_prompt(
            content=content,
            language=language,
            target_length=target_length,
            speakers=speakers,
        )
        
        script = llm_client.generate(prompt, temperature=0.7)
    
    # 台本の後処理
    script = _post_process_script(script)
    
    # ファイル保存
    script_path = output_dir / "script.md"
    script_path.write_text(script, encoding="utf-8")
    
    logger.info(f"台本生成完了: {script_path}")
    return script_path


def _merge_script_parts(script_parts: list[str]) -> str:
    """
    分割生成された台本パーツを結合
    
    Args:
        script_parts: 台本パーツのリスト
        
    Returns:
        結合された台本
    """
    if not script_parts:
        return ""
    
    if len(script_parts) == 1:
        return script_parts[0]
    
    # 台本の結合
    merged_script = []
    
    for i, part in enumerate(script_parts):
        if i == 0:
            # 最初のパーツはそのまま追加
            merged_script.append(part)
        else:
            # 2番目以降は導入部分を除去して追加
            cleaned_part = _remove_introduction(part)
            if cleaned_part:
                merged_script.append("\n\n" + cleaned_part)
    
    return "".join(merged_script)


def _remove_introduction(script: str) -> str:
    """
    台本から導入部分を除去
    
    Args:
        script: 台本テキスト
        
    Returns:
        導入部分を除去した台本
    """
    lines = script.split('\n')
    
    # 最初の数行の導入的な発言をスキップ
    start_index = 0
    for i, line in enumerate(lines):
        if line.strip() and not any(intro_word in line.lower() for intro_word in 
                                   ['こんにちは', 'はじめに', '今回は', 'welcome', 'hello']):
            start_index = i
            break
    
    return '\n'.join(lines[start_index:])


def _post_process_script(script: str) -> str:
    """
    台本の後処理
    
    Args:
        script: 生成された台本
        
    Returns:
        後処理済みの台本
    """
    # 不要な空行を除去
    lines = script.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 空行の連続を1つにまとめる
        if line.strip() == "":
            if not cleaned_lines or cleaned_lines[-1] != "":
                cleaned_lines.append("")
        else:
            cleaned_lines.append(line)
    
    # スピーカー表記の統一
    script = '\n'.join(cleaned_lines)
    
    # Speaker X: 形式に統一
    import re
    script = re.sub(r'(話者|スピーカー)\s*(\d+)\s*[:：]', r'Speaker \2:', script)
    script = re.sub(r'S(\d+)\s*[:：]', r'Speaker \1:', script)
    
    return script.strip() 