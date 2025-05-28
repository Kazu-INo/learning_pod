"""Gemini TTSクライアント"""

import mimetypes
import os
import struct
import time
from pathlib import Path
from typing import Dict, List, Optional

from google import genai
from google.genai import types

from learnpod.config import config
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


class TTSClient:
    """Gemini TTSクライアント"""
    
    def __init__(self, model_name: Optional[str] = None) -> None:
        """
        Args:
            model_name: 使用するモデル名（デフォルトは設定から取得）
        """
        self.model_name = model_name or config.tts_model
        
        # Gemini APIクライアントの初期化
        self.client = genai.Client(api_key=config.gemini_api_key)
        
        logger.info(f"TTSクライアント初期化完了: {self.model_name}")
    
    def generate_audio(
        self,
        text: str,
        speaker_configs: Dict[str, str],
        output_dir: Path,
        max_retries: int = 3,
    ) -> List[Path]:
        """
        マルチスピーカー音声生成
        
        Args:
            text: 台本テキスト（Speaker X: 形式）
            speaker_configs: スピーカー設定 {"S1": "Zephyr", "S2": "Puck"}
            output_dir: 出力ディレクトリ
            max_retries: 最大リトライ回数
            
        Returns:
            生成された音声ファイルのパスリスト
            
        Raises:
            Exception: 音声生成に失敗した場合
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # スピーカー設定の構築
        speaker_voice_configs = []
        for speaker_id, voice_name in speaker_configs.items():
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=speaker_id,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    ),
                )
            )
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_voice_configs
                ),
            ),
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"TTS生成開始 (試行 {attempt + 1}/{max_retries})")
                
                audio_files = []
                file_index = 0
                
                for chunk in self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                ):
                    if (
                        chunk.candidates is None
                        or chunk.candidates[0].content is None
                        or chunk.candidates[0].content.parts is None
                    ):
                        continue
                    
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        file_name = f"audio_chunk_{file_index}"
                        file_index += 1
                        
                        inline_data = part.inline_data
                        data_buffer = inline_data.data
                        file_extension = mimetypes.guess_extension(inline_data.mime_type)
                        
                        if file_extension is None:
                            file_extension = ".wav"
                            data_buffer = self._convert_to_wav(
                                inline_data.data, inline_data.mime_type
                            )
                        
                        audio_path = output_dir / f"{file_name}{file_extension}"
                        self._save_binary_file(audio_path, data_buffer)
                        audio_files.append(audio_path)
                    
                    elif chunk.text:
                        logger.debug(f"TTS応答テキスト: {chunk.text}")
                
                if audio_files:
                    logger.info(f"TTS生成成功: {len(audio_files)} ファイル")
                    return audio_files
                else:
                    raise ValueError("音声データが生成されませんでした")
                    
            except Exception as e:
                logger.warning(f"TTS生成失敗 (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    # 指数バックオフ
                    wait_time = 2 ** attempt
                    logger.info(f"{wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"TTS生成が最大リトライ回数に達しました: {e}")
                    raise
        
        raise Exception("TTS生成に失敗しました")
    
    def _save_binary_file(self, file_path: Path, data: bytes) -> None:
        """バイナリファイルの保存"""
        with open(file_path, "wb") as f:
            f.write(data)
        logger.debug(f"ファイル保存完了: {file_path}")
    
    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """
        音声データをWAV形式に変換
        
        Args:
            audio_data: 生の音声データ
            mime_type: 音声データのMIMEタイプ
            
        Returns:
            WAV形式の音声データ
        """
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size
        
        # WAVファイルヘッダーの生成
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize (total file size - 8 bytes)
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size (size of audio data)
        )
        
        return header + audio_data
    
    def _parse_audio_mime_type(self, mime_type: str) -> Dict[str, int]:
        """
        音声MIMEタイプからパラメータを解析
        
        Args:
            mime_type: 音声MIMEタイプ文字列
            
        Returns:
            bits_per_sampleとrateを含む辞書
        """
        bits_per_sample = 16
        rate = 24000
        
        # パラメータからレートを抽出
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass  # デフォルト値を維持
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass  # デフォルト値を維持
        
        return {"bits_per_sample": bits_per_sample, "rate": rate} 