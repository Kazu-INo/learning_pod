"""テキスト分割モジュール"""

import re
from typing import List

from learnpod.config import config
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


class TextSplitter:
    """テキスト分割クラス"""
    
    def __init__(self, chunk_size: int = None) -> None:
        """
        Args:
            chunk_size: チャンクサイズ（トークン数）
        """
        self.chunk_size = chunk_size or config.chunk_size
        logger.info(f"TextSplitter初期化: chunk_size={self.chunk_size}")
    
    def split_by_tokens(self, text: str, llm_client=None) -> List[str]:
        """
        トークン数に基づいてテキストを分割
        
        Args:
            text: 分割対象テキスト
            llm_client: トークンカウント用のLLMクライアント
            
        Returns:
            分割されたテキストのリスト
        """
        if llm_client and not llm_client.is_token_limit_exceeded(text, self.chunk_size):
            # トークン制限内の場合はそのまま返す
            return [text]
        
        # 段落単位で分割を試行
        paragraphs = self._split_by_paragraphs(text)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 段落を追加した場合のトークン数をチェック
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if llm_client:
                if llm_client.is_token_limit_exceeded(test_chunk, self.chunk_size):
                    # 制限を超える場合、現在のチャンクを保存
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph
                    else:
                        # 単一段落が制限を超える場合、文単位で分割
                        sentence_chunks = self._split_by_sentences(paragraph, llm_client)
                        chunks.extend(sentence_chunks)
                else:
                    current_chunk = test_chunk
            else:
                # LLMクライアントがない場合は概算で判定
                if self._estimate_tokens(test_chunk) > self.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph
                    else:
                        sentence_chunks = self._split_by_sentences(paragraph)
                        chunks.extend(sentence_chunks)
                else:
                    current_chunk = test_chunk
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"テキスト分割完了: {len(chunks)} チャンク")
        return chunks
    
    def split_script_for_tts(self, script: str) -> List[str]:
        """
        台本をTTS用に分割（スピーカー発言を保持）
        
        Args:
            script: 台本テキスト
            
        Returns:
            分割された台本チャンクのリスト
        """
        # スピーカー発言の抽出
        speaker_pattern = r'^(Speaker \d+|S\d+):\s*(.+)$'
        lines = script.split('\n')
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # スピーカー発言の解析
            match = re.match(speaker_pattern, line, re.MULTILINE)
            if match:
                speaker, content = match.groups()
                line_tokens = self._estimate_tokens(line)
                
                # チャンクサイズを超える場合
                if current_tokens + line_tokens > self.chunk_size and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_tokens = line_tokens
                else:
                    current_chunk.append(line)
                    current_tokens += line_tokens
            else:
                # スピーカー発言以外の行（説明など）
                current_chunk.append(line)
                current_tokens += self._estimate_tokens(line)
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        logger.info(f"台本分割完了: {len(chunks)} チャンク")
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """段落単位でテキストを分割"""
        # 空行で段落を分割
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_by_sentences(self, text: str, llm_client=None) -> List[str]:
        """文単位でテキストを分割"""
        # 日本語の文区切り
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() + '。' for s in sentences if s.strip()]
        
        if not sentences:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence if current_chunk else sentence
            
            if llm_client:
                if llm_client.is_token_limit_exceeded(test_chunk, self.chunk_size):
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        # 単一文が制限を超える場合はそのまま追加
                        chunks.append(sentence)
                else:
                    current_chunk = test_chunk
            else:
                if self._estimate_tokens(test_chunk) > self.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        chunks.append(sentence)
                else:
                    current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """トークン数の概算"""
        # 日本語の場合、文字数の約0.7倍がトークン数の概算
        return int(len(text) * 0.7) 