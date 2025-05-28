"""設定管理モジュール"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """アプリケーション設定クラス"""
    
    def __init__(self) -> None:
        # 環境変数が設定されていない場合のみ.envファイルを読み込み
        if not os.getenv("GEMINI_API_KEY"):
            env_path = Path(".env")
            if env_path.exists():
                load_dotenv(env_path)
        
        # Gemini API設定
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        
        # Gmail設定（オプション）
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_PASSWORD")
        self.gmail_to = os.getenv("GMAIL_TO")
        
        # デフォルト設定
        self.default_language = "ja"
        self.default_length = 20
        self.default_speakers = {"S1": "Sakura", "S2": "Taro"}
        self.default_voice_map = {"S1": "Zephyr", "S2": "Puck"}
        
        # LLMモデル設定
        self.llm_model = "gemini-2.5-flash-preview-05-20"
        self.tts_model = "gemini-2.5-flash-preview-tts"
        
        # 音声設定
        self.chunk_size = 800  # トークン数
        self.target_words = (2000, 3000)  # 台本の目標語数
        
    @property
    def has_gmail_config(self) -> bool:
        """Gmail設定が完了しているかチェック"""
        return all([self.gmail_user, self.gmail_password, self.gmail_to])
    
    def get_output_dir(self, timestamp: Optional[str] = None) -> Path:
        """出力ディレクトリのパスを取得"""
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%y%m%d_%H%M")
        
        base_dir = Path("outputs") / timestamp
        
        # ディレクトリ衝突の回避
        counter = 1
        original_dir = base_dir
        while base_dir.exists():
            base_dir = Path(f"{original_dir}_{counter}")
            counter += 1
            
        return base_dir


class ConfigProxy:
    """設定プロキシクラス（遅延初期化）"""
    
    def __init__(self):
        self._config: Optional[Config] = None
    
    def _get_config(self) -> Config:
        """設定インスタンスを取得（遅延初期化）"""
        if self._config is None:
            self._config = Config()
        return self._config
    
    def __getattr__(self, name):
        """属性アクセスを設定インスタンスに委譲"""
        return getattr(self._get_config(), name)


# グローバル設定インスタンス（遅延初期化）
config = ConfigProxy() 