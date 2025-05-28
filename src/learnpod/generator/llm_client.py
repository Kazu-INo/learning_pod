"""Gemini LLMクライアント"""

import time
from typing import Optional

from google import genai
from google.genai import types

from learnpod.config import config
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Gemini LLMクライアント"""
    
    def __init__(self, model_name: Optional[str] = None) -> None:
        """
        Args:
            model_name: 使用するモデル名（デフォルトは設定から取得）
        """
        self.model_name = model_name or config.llm_model
        
        # Gemini APIクライアントの初期化
        self.client = genai.Client(api_key=config.gemini_api_key)
        
        logger.info(f"LLMクライアント初期化完了: {self.model_name}")
    
    def generate(
        self,
        prompt: str,
        max_retries: int = 3,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """
        テキスト生成
        
        Args:
            prompt: 入力プロンプト
            max_retries: 最大リトライ回数
            temperature: 生成の創造性（0.0-1.0）
            max_output_tokens: 最大出力トークン数
            
        Returns:
            生成されたテキスト
            
        Raises:
            Exception: 生成に失敗した場合
        """
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="text/plain",
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM生成開始 (試行 {attempt + 1}/{max_retries})")
                
                # 通常の生成を使用
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                )
                
                if response.text:
                    logger.info(f"LLM生成成功: {len(response.text)} 文字")
                    return response.text
                else:
                    raise ValueError("空のレスポンスが返されました")
                    
            except Exception as e:
                logger.warning(f"LLM生成失敗 (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    # 指数バックオフ
                    wait_time = 2 ** attempt
                    logger.info(f"{wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM生成が最大リトライ回数に達しました: {e}")
                    raise
        
        raise Exception("LLM生成に失敗しました")
    
    def count_tokens(self, text: str) -> int:
        """
        テキストのトークン数を概算
        
        Args:
            text: 対象テキスト
            
        Returns:
            概算トークン数
        """
        try:
            # 新しいAPIでのトークンカウント
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=text)],
                ),
            ]
            
            response = self.client.models.count_tokens(
                model=self.model_name,
                contents=contents,
            )
            return response.total_tokens
        except Exception as e:
            logger.warning(f"トークンカウント失敗、概算値を使用: {e}")
            # 日本語の場合、文字数の約0.7倍がトークン数の概算
            return int(len(text) * 0.7)
    
    def is_token_limit_exceeded(self, text: str, limit: int = 30000) -> bool:
        """
        トークン制限を超過しているかチェック
        
        Args:
            text: 対象テキスト
            limit: トークン制限数
            
        Returns:
            制限を超過している場合True
        """
        token_count = self.count_tokens(text)
        logger.debug(f"トークン数: {token_count}/{limit}")
        return token_count > limit 