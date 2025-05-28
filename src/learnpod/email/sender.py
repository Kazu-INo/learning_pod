"""メール送信モジュール"""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from learnpod.config import config
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


def send_email(
    output_dir: Path,
    title: str,
    audio_path: Optional[Path] = None,
    script_path: Optional[Path] = None,
    explanation_path: Optional[Path] = None,
    qa_path: Optional[Path] = None,
    flashcard_path: Optional[Path] = None,
) -> bool:
    """
    生成されたコンテンツをメールで送信
    
    Args:
        output_dir: 出力ディレクトリ
        title: ポッドキャストのタイトル
        audio_path: 音声ファイルのパス
        script_path: 台本ファイルのパス
        explanation_path: 詳細解説ファイルのパス
        qa_path: Q&Aファイルのパス
        flashcard_path: フラッシュカードファイルのパス
        
    Returns:
        送信成功時True
    """
    if not config.has_gmail_config:
        logger.warning("Gmail設定が不完全です。メール送信をスキップします。")
        return False
    
    logger.info(f"メール送信開始: {title}")
    
    try:
        # メッセージの作成
        msg = _create_message(
            title=title,
            audio_path=audio_path,
            script_path=script_path,
            explanation_path=explanation_path,
            qa_path=qa_path,
            flashcard_path=flashcard_path,
        )
        
        # SMTP接続とメール送信
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.gmail_user, config.gmail_password)
            server.send_message(msg)
        
        logger.info("メール送信完了")
        return True
        
    except Exception as e:
        logger.error(f"メール送信に失敗: {e}")
        return False


def _create_message(
    title: str,
    audio_path: Optional[Path] = None,
    script_path: Optional[Path] = None,
    explanation_path: Optional[Path] = None,
    qa_path: Optional[Path] = None,
    flashcard_path: Optional[Path] = None,
) -> MIMEMultipart:
    """
    メールメッセージを作成
    
    Args:
        title: ポッドキャストのタイトル
        audio_path: 音声ファイルのパス
        script_path: 台本ファイルのパス
        explanation_path: 詳細解説ファイルのパス
        qa_path: Q&Aファイルのパス
        flashcard_path: フラッシュカードファイルのパス
        
    Returns:
        メールメッセージ
    """
    msg = MIMEMultipart()
    msg["From"] = config.gmail_user
    msg["To"] = config.gmail_to
    msg["Subject"] = f"LearnPod: {title}"
    
    # メール本文の作成
    body = _create_email_body(
        title=title,
        audio_path=audio_path,
        script_path=script_path,
        explanation_path=explanation_path,
        qa_path=qa_path,
        flashcard_path=flashcard_path,
    )
    
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    # ファイルの添付
    attachments = [
        ("音声ファイル", audio_path),
        ("台本", script_path),
        ("詳細解説", explanation_path),
        ("Q&A", qa_path),
        ("フラッシュカード", flashcard_path),
    ]
    
    for description, file_path in attachments:
        if file_path and file_path.exists():
            _attach_file(msg, file_path, description)
    
    return msg


def _create_email_body(
    title: str,
    audio_path: Optional[Path] = None,
    script_path: Optional[Path] = None,
    explanation_path: Optional[Path] = None,
    qa_path: Optional[Path] = None,
    flashcard_path: Optional[Path] = None,
) -> str:
    """
    メール本文を作成
    
    Args:
        title: ポッドキャストのタイトル
        audio_path: 音声ファイルのパス
        script_path: 台本ファイルのパス
        explanation_path: 詳細解説ファイルのパス
        qa_path: Q&Aファイルのパス
        flashcard_path: フラッシュカードファイルのパス
        
    Returns:
        メール本文
    """
    body_parts = [
        f"LearnPodで生成されたコンテンツをお送りします。",
        f"",
        f"タイトル: {title}",
        f"生成日時: {_get_current_datetime()}",
        f"",
        f"【添付ファイル】",
    ]
    
    # 添付ファイルの説明
    if audio_path and audio_path.exists():
        duration = _get_audio_duration(audio_path)
        body_parts.append(f"🎧 音声ファイル ({audio_path.name}) - {duration}")
    
    if script_path and script_path.exists():
        word_count = _get_file_word_count(script_path)
        body_parts.append(f"📝 台本 ({script_path.name}) - 約{word_count}語")
    
    if explanation_path and explanation_path.exists():
        word_count = _get_file_word_count(explanation_path)
        body_parts.append(f"📖 詳細解説 ({explanation_path.name}) - 約{word_count}語")
    
    if qa_path and qa_path.exists():
        qa_count = _get_qa_count(qa_path)
        body_parts.append(f"❓ Q&A ({qa_path.name}) - {qa_count}問")
    
    if flashcard_path and flashcard_path.exists():
        flashcard_count = _get_flashcard_count(flashcard_path)
        body_parts.append(f"🗂️ フラッシュカード ({flashcard_path.name}) - {flashcard_count}枚")
    
    body_parts.extend([
        f"",
        f"【使用方法】",
        f"1. 音声ファイルを再生してポッドキャストを聞く",
        f"2. 台本と詳細解説で理解を深める",
        f"3. Q&Aで理解度をチェック",
        f"4. フラッシュカードで重要用語を復習",
        f"",
        f"学習にお役立てください！",
        f"",
        f"---",
        f"LearnPod v0.2.0",
        f"https://github.com/your-repo/learnpod",
    ])
    
    return "\n".join(body_parts)


def _attach_file(msg: MIMEMultipart, file_path: Path, description: str) -> None:
    """
    ファイルをメールに添付
    
    Args:
        msg: メールメッセージ
        file_path: 添付ファイルのパス
        description: ファイルの説明
    """
    try:
        with open(file_path, "rb") as f:
            attachment = MIMEApplication(f.read())
        
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=file_path.name
        )
        
        msg.attach(attachment)
        logger.debug(f"ファイル添付完了: {description} ({file_path.name})")
        
    except Exception as e:
        logger.warning(f"ファイル添付失敗: {description} - {e}")


def _get_current_datetime() -> str:
    """現在の日時を取得"""
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日 %H:%M")


def _get_audio_duration(audio_path: Path) -> str:
    """音声ファイルの長さを取得"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(audio_path))
        duration_seconds = len(audio) / 1000
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        return f"{minutes}分{seconds}秒"
    except Exception:
        return "不明"


def _get_file_word_count(file_path: Path) -> int:
    """ファイルの語数を取得（概算）"""
    try:
        content = file_path.read_text(encoding="utf-8")
        # 日本語の場合、文字数を語数として概算
        return len(content.replace(" ", "").replace("\n", ""))
    except Exception:
        return 0


def _get_qa_count(qa_path: Path) -> int:
    """Q&Aの問題数を取得"""
    try:
        content = qa_path.read_text(encoding="utf-8")
        import re
        matches = re.findall(r'\*\*Q\d+:', content)
        return len(matches)
    except Exception:
        return 0


def _get_flashcard_count(flashcard_path: Path) -> int:
    """フラッシュカードの枚数を取得"""
    try:
        import yaml
        content = flashcard_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if isinstance(data, dict) and "flashcards" in data:
            return len(data["flashcards"])
        return 0
    except Exception:
        return 0 