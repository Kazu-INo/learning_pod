"""Markdown取り込みモジュール"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IngestedDoc:
    """取り込み済みドキュメント"""
    
    title: str
    raw_md: str
    sections: List[Dict[str, str]]
    metadata: Optional[Dict] = None
    
    def get_content_without_metadata(self) -> str:
        """メタデータを除いたコンテンツを取得"""
        if self.metadata:
            # YAML Front-Matterを除去
            content = re.sub(r'^---\n.*?\n---\n', '', self.raw_md, flags=re.DOTALL)
            return content.strip()
        return self.raw_md
    
    def get_section_by_level(self, level: int) -> List[Dict[str, str]]:
        """指定レベルのセクションを取得"""
        return [s for s in self.sections if s["level"] == level]
    
    def get_total_word_count(self) -> int:
        """総語数を取得（概算）"""
        content = self.get_content_without_metadata()
        # 日本語の場合、文字数を語数として概算
        return len(content.replace(" ", "").replace("\n", ""))


def ingest_markdown(file_path: Path) -> IngestedDoc:
    """
    Markdownファイルを取り込み
    
    Args:
        file_path: Markdownファイルのパス
        
    Returns:
        取り込み済みドキュメント
        
    Raises:
        FileNotFoundError: ファイルが見つからない場合
        ValueError: ファイル形式が不正な場合
    """
    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    if file_path.suffix.lower() != ".md":
        raise ValueError(f"Markdownファイルではありません: {file_path}")
    
    logger.info(f"Markdown取り込み開始: {file_path}")
    
    # ファイル内容の読み込み
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"ファイルの文字エンコーディングが不正です: {e}")
    
    if not content.strip():
        raise ValueError("ファイルが空です")
    
    # YAML Front-Matterの解析
    metadata = None
    if content.startswith("---\n"):
        try:
            yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
                metadata = yaml.safe_load(yaml_content)
                logger.debug(f"YAML Front-Matter解析完了: {metadata}")
        except yaml.YAMLError as e:
            logger.warning(f"YAML Front-Matter解析失敗: {e}")
    
    # タイトルの抽出
    title = _extract_title(content, metadata, file_path)
    
    # セクションの分割
    sections = _extract_sections(content)
    
    doc = IngestedDoc(
        title=title,
        raw_md=content,
        sections=sections,
        metadata=metadata,
    )
    
    logger.info(
        f"Markdown取り込み完了: タイトル='{title}', "
        f"セクション数={len(sections)}, 語数={doc.get_total_word_count()}"
    )
    
    return doc


def _extract_title(content: str, metadata: Optional[Dict], file_path: Path) -> str:
    """タイトルを抽出"""
    # 1. メタデータからタイトルを取得
    if metadata and "title" in metadata:
        return str(metadata["title"])
    
    # 2. 最初のH1見出しを取得
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # 3. ファイル名をタイトルとして使用
    return file_path.stem


def _extract_sections(content: str) -> List[Dict[str, str]]:
    """セクションを抽出"""
    sections = []
    
    # 見出しパターン（H1-H3）
    heading_pattern = r'^(#{1,3})\s+(.+)$'
    
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        heading_match = re.match(heading_pattern, line)
        
        if heading_match:
            # 前のセクションを保存
            if current_section:
                current_section["content"] = '\n'.join(current_content).strip()
                sections.append(current_section)
            
            # 新しいセクションを開始
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            
            current_section = {
                "level": level,
                "title": title,
                "content": "",
            }
            current_content = []
        else:
            # セクション内容を蓄積
            if current_section:
                current_content.append(line)
    
    # 最後のセクションを保存
    if current_section:
        current_section["content"] = '\n'.join(current_content).strip()
        sections.append(current_section)
    
    # セクションがない場合、全体を1つのセクションとして扱う
    if not sections:
        sections.append({
            "level": 1,
            "title": "本文",
            "content": content,
        })
    
    logger.debug(f"セクション抽出完了: {len(sections)} セクション")
    return sections 