"""LearnPod CLI インターフェース"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import click

from learnpod.config import config
from learnpod.pipeline.orchestrator import PipelineOrchestrator
from learnpod.utils.logger import setup_logging


def _parse_speakers(speakers_str: str) -> Dict[str, str]:
    """スピーカー設定文字列を解析"""
    speakers = {}
    for pair in speakers_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            speakers[key.strip()] = value.strip()
    return speakers


@click.group()
@click.version_option(version="0.2.0")
@click.option("--verbose", "-v", is_flag=True, help="詳細ログを表示")
def main(verbose: bool) -> None:
    """LearnPod - 学習・研究アウトプットからポッドキャスト音声とQ&Aセットを自動生成"""
    # ログレベルの設定
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--length", default=20, help="音声の長さ（分）")
@click.option("--lang", default="ja", help="言語設定")
@click.option(
    "--speakers",
    default="Speaker 1=Sakura,Speaker 2=Taro",
    help="スピーカー設定（例: Speaker 1=Sakura,Speaker 2=Taro）",
)
@click.option(
    "--voices",
    default="Speaker 1=Zephyr,Speaker 2=Puck",
    help="音声設定（例: Speaker 1=Zephyr,Speaker 2=Puck）",
)
@click.option("--no-email", is_flag=True, help="メール送信をスキップ")
@click.option("--all", "run_all", is_flag=True, help="全パイプラインを実行")
def run(
    input_file: Path,
    length: int,
    lang: str,
    speakers: str,
    voices: str,
    no_email: bool,
    run_all: bool,
) -> None:
    """Markdownファイルからポッドキャストコンテンツを生成"""
    
    try:
        # 設定の解析
        speaker_config = _parse_speakers(speakers)
        voice_config = _parse_speakers(voices)
        
        # パイプラインの実行
        orchestrator = PipelineOrchestrator()
        
        output_dir = orchestrator.run_full_pipeline(
            input_file=input_file,
            language=lang,
            target_length=length,
            speakers=speaker_config,
            voice_map=voice_config,
            send_mail=not no_email,
        )
        
        click.echo(f"✅ 生成完了: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def ingest(input_file: Path) -> None:
    """Markdownファイルを取り込み、内容を確認"""
    
    try:
        from learnpod.pipeline.ingest import ingest_markdown
        
        doc = ingest_markdown(input_file)
        
        click.echo(f"📄 ファイル: {input_file}")
        click.echo(f"📝 タイトル: {doc.title}")
        click.echo(f"📊 セクション数: {len(doc.sections)}")
        click.echo(f"📏 総語数: {doc.get_total_word_count()}")
        
        if doc.metadata:
            click.echo(f"🏷️  メタデータ: {doc.metadata}")
        
        click.echo("\n📋 セクション一覧:")
        for i, section in enumerate(doc.sections, 1):
            level_indicator = "  " * (section["level"] - 1) + "•"
            click.echo(f"{level_indicator} H{section['level']}: {section['title']}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--length", default=20, help="音声の長さ（分）")
@click.option("--lang", default="ja", help="言語設定")
@click.option(
    "--speakers",
    default="Speaker 1=Sakura,Speaker 2=Taro",
    help="スピーカー設定",
)
def script(
    input_file: Path,
    length: int,
    lang: str,
    speakers: str,
) -> None:
    """台本のみを生成"""
    
    try:
        from learnpod.pipeline.ingest import ingest_markdown
        from learnpod.pipeline.build_script import build_script
        
        # 出力ディレクトリの準備
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = Path("outputs") / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Markdown取り込み
        doc = ingest_markdown(input_file)
        
        # スピーカー設定の解析
        speaker_config = _parse_speakers(speakers)
        
        # 台本生成
        script_path = build_script(
            doc=doc,
            output_dir=output_dir,
            language=lang,
            target_length=length,
            speakers=speaker_config,
        )
        
        click.echo(f"✅ 台本生成完了: {script_path}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("script_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--voices",
    default="Speaker 1=Zephyr,Speaker 2=Puck",
    help="音声設定",
)
def audio(script_file: Path, voices: str) -> None:
    """台本から音声を生成"""
    
    try:
        from learnpod.pipeline.build_audio import build_audio
        
        # 出力ディレクトリの準備
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = Path("outputs") / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 音声設定の解析
        voice_config = _parse_speakers(voices)
        
        # 音声生成
        audio_path = build_audio(
            script_path=script_file,
            output_dir=output_dir,
            speaker_configs=voice_config,
        )
        
        if audio_path:
            click.echo(f"✅ 音声生成完了: {audio_path}")
        else:
            click.echo("❌ 音声生成に失敗しました", err=True)
            raise click.Abort()
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("script_file", type=click.Path(exists=True, path_type=Path))
def questions(script_file: Path) -> None:
    """台本からQ&Aとフラッシュカードを生成"""
    
    try:
        from learnpod.pipeline.build_questions import build_questions
        
        # 出力ディレクトリの準備
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = Path("outputs") / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Q&A生成
        qa_path, flashcard_path = build_questions(
            script_path=script_file,
            output_dir=output_dir,
        )
        
        click.echo(f"✅ Q&A生成完了: {qa_path}")
        if flashcard_path:
            click.echo(f"✅ フラッシュカード生成完了: {flashcard_path}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        raise click.Abort()


@main.command()
def config_check() -> None:
    """設定を確認"""
    
    click.echo("🔧 LearnPod 設定確認")
    click.echo("=" * 30)
    
    # API設定
    if config.gemini_api_key:
        click.echo("✅ Gemini API Key: 設定済み")
    else:
        click.echo("❌ Gemini API Key: 未設定")
    
    # Gmail設定
    if config.has_gmail_config:
        click.echo("✅ Gmail設定: 完了")
        click.echo(f"   送信者: {config.gmail_user}")
        click.echo(f"   宛先: {config.gmail_to}")
    else:
        click.echo("⚠️  Gmail設定: 不完全（メール送信は無効）")
    
    # モデル設定
    click.echo(f"🤖 LLMモデル: {config.llm_model}")
    click.echo(f"🎤 TTSモデル: {config.tts_model}")
    
    # その他設定
    click.echo(f"📏 チャンクサイズ: {config.chunk_size} トークン")
    click.echo(f"🎯 目標語数: {config.target_words[0]}-{config.target_words[1]} 語")


if __name__ == "__main__":
    main() 