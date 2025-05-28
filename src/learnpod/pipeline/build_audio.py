"""音声生成モジュール"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from pydub import AudioSegment

from learnpod.generator import TTSClient, TextSplitter
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


def build_audio(
    script_path: Path,
    output_dir: Path,
    speaker_configs: Optional[Dict[str, str]] = None,
) -> Optional[Path]:
    """
    音声を生成
    
    Args:
        script_path: 台本ファイルのパス
        output_dir: 出力ディレクトリ
        speaker_configs: スピーカー設定 {"S1": "Zephyr", "S2": "Puck"}
        
    Returns:
        生成された音声ファイルのパス（失敗時はNone）
    """
    logger.info(f"音声生成開始: {script_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # デフォルトスピーカー設定
    if speaker_configs is None:
        speaker_configs = {"Speaker 1": "Zephyr", "Speaker 2": "Puck"}
    
    # 台本の読み込み
    script_content = script_path.read_text(encoding="utf-8")
    
    # TTSクライアントの初期化
    tts_client = TTSClient()
    
    # 台本の分割
    splitter = TextSplitter()
    script_chunks = splitter.split_script_for_tts(script_content)
    
    logger.info(f"台本を {len(script_chunks)} チャンクに分割しました")
    
    # 各チャンクで音声生成
    audio_files = []
    for i, chunk in enumerate(script_chunks):
        logger.info(f"音声生成中: チャンク {i+1}/{len(script_chunks)}")
        
        try:
            chunk_audio_files = tts_client.generate_audio(
                text=chunk,
                speaker_configs=speaker_configs,
                output_dir=output_dir / "chunks",
            )
            audio_files.extend(chunk_audio_files)
        except Exception as e:
            logger.error(f"チャンク {i+1} の音声生成に失敗: {e}")
            continue
    
    if not audio_files:
        logger.error("音声ファイルが生成されませんでした")
        return None
    
    # 音声ファイルの結合
    combined_audio_path = _combine_audio_files(audio_files, output_dir)
    
    if combined_audio_path is None:
        logger.error("音声ファイルの結合に失敗しました")
        return None
    
    # MP3変換
    mp3_path = _convert_to_mp3(combined_audio_path, output_dir)
    
    # 一時ファイルのクリーンアップ
    _cleanup_temp_files(output_dir / "chunks")
    
    final_path = mp3_path if mp3_path else combined_audio_path
    logger.info(f"音声生成完了: {final_path}")
    
    return final_path


def _combine_audio_files(audio_files: List[Path], output_dir: Path) -> Optional[Path]:
    """
    音声ファイルを結合
    
    Args:
        audio_files: 音声ファイルのリスト
        output_dir: 出力ディレクトリ
        
    Returns:
        結合された音声ファイルのパス
    """
    if not audio_files:
        return None
    
    if len(audio_files) == 1:
        # ファイルが1つの場合はコピー
        combined_path = output_dir / "podcast.wav"
        combined_path.write_bytes(audio_files[0].read_bytes())
        return combined_path
    
    try:
        # pydubを使用して音声ファイルを結合
        combined_audio = AudioSegment.empty()
        
        for audio_file in audio_files:
            logger.debug(f"音声ファイル結合中: {audio_file}")
            
            # ファイル形式の自動検出
            if audio_file.suffix.lower() == '.wav':
                audio_segment = AudioSegment.from_wav(str(audio_file))
            elif audio_file.suffix.lower() == '.mp3':
                audio_segment = AudioSegment.from_mp3(str(audio_file))
            else:
                # 不明な形式の場合はWAVとして試行
                audio_segment = AudioSegment.from_wav(str(audio_file))
            
            combined_audio += audio_segment
        
        # 結合された音声を保存
        combined_path = output_dir / "podcast.wav"
        combined_audio.export(str(combined_path), format="wav")
        
        logger.info(f"音声ファイル結合完了: {len(audio_files)} ファイル")
        return combined_path
        
    except Exception as e:
        logger.error(f"音声ファイル結合に失敗: {e}")
        return None


def _convert_to_mp3(wav_path: Path, output_dir: Path) -> Optional[Path]:
    """
    WAVファイルをMP3に変換
    
    Args:
        wav_path: WAVファイルのパス
        output_dir: 出力ディレクトリ
        
    Returns:
        MP3ファイルのパス（失敗時はNone）
    """
    mp3_path = output_dir / "podcast.mp3"
    
    # FFmpegを使用した変換を試行
    if _convert_with_ffmpeg(wav_path, mp3_path):
        return mp3_path
    
    # FFmpegが失敗した場合、pydubで変換を試行
    if _convert_with_pydub(wav_path, mp3_path):
        return mp3_path
    
    logger.warning("MP3変換に失敗しました。WAVファイルを使用してください。")
    return None


def _convert_with_ffmpeg(wav_path: Path, mp3_path: Path) -> bool:
    """
    FFmpegを使用してMP3に変換
    
    Args:
        wav_path: WAVファイルのパス
        mp3_path: MP3ファイルのパス
        
    Returns:
        変換成功時True
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", str(wav_path),
            "-codec:a", "libmp3lame",
            "-b:a", "192k",
            "-y",  # 上書き許可
            str(mp3_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分でタイムアウト
        )
        
        if result.returncode == 0:
            logger.info("FFmpegでMP3変換完了")
            return True
        else:
            logger.warning(f"FFmpeg変換失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.warning("FFmpeg変換がタイムアウトしました")
        return False
    except FileNotFoundError:
        logger.warning("FFmpegが見つかりません")
        return False
    except Exception as e:
        logger.warning(f"FFmpeg変換でエラー: {e}")
        return False


def _convert_with_pydub(wav_path: Path, mp3_path: Path) -> bool:
    """
    pydubを使用してMP3に変換
    
    Args:
        wav_path: WAVファイルのパス
        mp3_path: MP3ファイルのパス
        
    Returns:
        変換成功時True
    """
    try:
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3", bitrate="192k")
        logger.info("pydubでMP3変換完了")
        return True
    except Exception as e:
        logger.warning(f"pydub変換でエラー: {e}")
        return False


def _cleanup_temp_files(temp_dir: Path) -> None:
    """
    一時ファイルをクリーンアップ
    
    Args:
        temp_dir: 一時ディレクトリ
    """
    if temp_dir.exists():
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.debug(f"一時ファイルクリーンアップ完了: {temp_dir}")
        except Exception as e:
            logger.warning(f"一時ファイルクリーンアップ失敗: {e}") 