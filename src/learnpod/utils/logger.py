"""ログ機能モジュール"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    ロガーを取得
    
    Args:
        name: ロガー名
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        
    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)
    
    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger
    
    # ログレベルの設定
    if level is None:
        level = "INFO"
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # ハンドラーをロガーに追加
    logger.addHandler(console_handler)
    
    # 親ロガーへの伝播を防ぐ
    logger.propagate = False
    
    return logger


def setup_logging(level: str = "INFO") -> None:
    """
    アプリケーション全体のログ設定
    
    Args:
        level: ログレベル
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 外部ライブラリのログレベルを調整
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING) 