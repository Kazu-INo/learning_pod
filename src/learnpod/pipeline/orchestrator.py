"""パイプライン統括モジュール"""

from pathlib import Path
from typing import Dict, Optional, Tuple

from learnpod.config import config
from learnpod.email import send_email
from learnpod.pipeline.build_audio import build_audio
from learnpod.pipeline.build_explainer import build_explainer
from learnpod.pipeline.build_questions import build_questions
from learnpod.pipeline.build_script import build_script
from learnpod.pipeline.ingest import IngestedDoc, ingest_markdown
from learnpod.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    """パイプライン統括クラス"""
    
    def __init__(self) -> None:
        self.doc: Optional[IngestedDoc] = None
        self.output_dir: Optional[Path] = None
        self.results: Dict[str, Optional[Path]] = {
            "script": None,
            "explanation": None,
            "questions": None,
            "flashcards": None,
            "audio": None,
        }
    
    def run_full_pipeline(
        self,
        input_file: Path,
        language: str = "ja",
        target_length: int = 20,
        speakers: Optional[Dict[str, str]] = None,
        voice_map: Optional[Dict[str, str]] = None,
        send_mail: bool = True,
        timestamp: Optional[str] = None,
    ) -> Path:
        """
        フルパイプラインを実行
        
        Args:
            input_file: 入力Markdownファイル
            language: 言語設定
            target_length: 目標時間（分）
            speakers: スピーカー設定
            voice_map: 音声マッピング
            send_mail: メール送信フラグ
            timestamp: タイムスタンプ（出力ディレクトリ用）
            
        Returns:
            出力ディレクトリのパス
        """
        logger.info(f"フルパイプライン開始: {input_file}")
        
        # 出力ディレクトリの準備
        self.output_dir = config.get_output_dir(timestamp)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Markdown取り込み
            self.doc = self.ingest_step(input_file)
            
            # 2. 台本生成
            script_path = self.build_script_step(language, target_length, speakers)
            
            # 3. 詳細解説生成
            explanation_path = self.build_explainer_step(script_path)
            
            # 4. Q&A生成
            qa_path, flashcard_path = self.build_questions_step(script_path)
            
            # 5. 音声生成
            audio_path = self.build_audio_step(script_path, voice_map)
            
            # 6. メール送信
            if send_mail:
                self.send_email_step()
            
            # 実行サマリーの出力
            self._print_summary()
            
            logger.info(f"フルパイプライン完了: {self.output_dir}")
            return self.output_dir
            
        except Exception as e:
            logger.error(f"パイプライン実行中にエラーが発生: {e}")
            raise
    
    def ingest_step(self, input_file: Path) -> IngestedDoc:
        """Markdown取り込みステップ"""
        logger.info("ステップ 1/6: Markdown取り込み")
        
        doc = ingest_markdown(input_file)
        
        # 入力ファイルのコピー
        input_copy = self.output_dir / f"input_{input_file.name}"
        input_copy.write_text(doc.raw_md, encoding="utf-8")
        
        return doc
    
    def build_script_step(
        self,
        language: str,
        target_length: int,
        speakers: Optional[Dict[str, str]],
    ) -> Path:
        """台本生成ステップ"""
        logger.info("ステップ 2/6: 台本生成")
        
        script_path = build_script(
            doc=self.doc,
            output_dir=self.output_dir,
            language=language,
            target_length=target_length,
            speakers=speakers,
        )
        
        self.results["script"] = script_path
        return script_path
    
    def build_explainer_step(self, script_path: Path) -> Path:
        """詳細解説生成ステップ"""
        logger.info("ステップ 3/6: 詳細解説生成")
        
        explanation_path = build_explainer(
            script_path=script_path,
            output_dir=self.output_dir,
        )
        
        self.results["explanation"] = explanation_path
        return explanation_path
    
    def build_questions_step(self, script_path: Path) -> Tuple[Path, Optional[Path]]:
        """Q&A生成ステップ"""
        logger.info("ステップ 4/6: Q&A生成")
        
        qa_path, flashcard_path = build_questions(
            script_path=script_path,
            output_dir=self.output_dir,
        )
        
        self.results["questions"] = qa_path
        self.results["flashcards"] = flashcard_path
        return qa_path, flashcard_path
    
    def build_audio_step(
        self,
        script_path: Path,
        voice_map: Optional[Dict[str, str]],
    ) -> Optional[Path]:
        """音声生成ステップ"""
        logger.info("ステップ 5/6: 音声生成")
        
        try:
            audio_path = build_audio(
                script_path=script_path,
                output_dir=self.output_dir,
                speaker_configs=voice_map,
            )
            
            self.results["audio"] = audio_path
            return audio_path
            
        except Exception as e:
            logger.error(f"音声生成に失敗: {e}")
            logger.info("音声生成をスキップして続行します")
            return None
    
    def send_email_step(self) -> bool:
        """メール送信ステップ"""
        logger.info("ステップ 6/6: メール送信")
        
        try:
            success = send_email(
                output_dir=self.output_dir,
                title=self.doc.title,
                audio_path=self.results["audio"],
                script_path=self.results["script"],
                explanation_path=self.results["explanation"],
                qa_path=self.results["questions"],
                flashcard_path=self.results["flashcards"],
            )
            
            return success
            
        except Exception as e:
            logger.error(f"メール送信に失敗: {e}")
            return False
    
    def _print_summary(self) -> None:
        """実行サマリーを出力"""
        logger.info("=" * 50)
        logger.info("パイプライン実行サマリー")
        logger.info("=" * 50)
        logger.info(f"タイトル: {self.doc.title}")
        logger.info(f"出力ディレクトリ: {self.output_dir}")
        logger.info("")
        logger.info("生成されたファイル:")
        
        for step_name, file_path in self.results.items():
            if file_path and file_path.exists():
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                if step_name == "audio":
                    # 音声ファイルの場合は時間も表示
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(str(file_path))
                        duration_seconds = len(audio) / 1000
                        minutes = int(duration_seconds // 60)
                        seconds = int(duration_seconds % 60)
                        logger.info(f"  ✅ {step_name}: {file_path.name} ({size_mb:.1f}MB, {minutes}:{seconds:02d})")
                    except Exception:
                        logger.info(f"  ✅ {step_name}: {file_path.name} ({size_mb:.1f}MB)")
                else:
                    logger.info(f"  ✅ {step_name}: {file_path.name} ({size_mb:.1f}MB)")
            else:
                logger.info(f"  ❌ {step_name}: 生成されませんでした")
        
        logger.info("")
        logger.info("パイプライン実行完了！")
        logger.info("=" * 50) 