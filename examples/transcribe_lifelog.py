#!/usr/bin/env python3
"""
Limitless Lifelog の音声を文字起こしするサンプル

OpenAI Whisper API を使用して、Lifelog の音声を自動で文字起こしします。

必要な環境変数:
    - LIMITLESS_API_KEY: Limitless API キー
    - OPENAI_API_KEY: OpenAI API キー

実行方法:
    # Lifelog 一覧を表示
    python examples/transcribe_lifelog.py --list

    # 特定の Lifelog を文字起こし
    python examples/transcribe_lifelog.py <lifelog_id>

    # 音声ファイルも保持する場合
    python examples/transcribe_lifelog.py <lifelog_id> --keep-audio

    # 出力ディレクトリを指定
    python examples/transcribe_lifelog.py <lifelog_id> --output ./transcriptions
"""

import sys
import argparse
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def main():
    """Lifelog の音声を文字起こし"""

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Limitless Lifelog の音声を OpenAI Whisper API で文字起こし"
    )
    parser.add_argument(
        "lifelog_id",
        type=str,
        nargs="?",
        help="文字起こしする Lifelog の ID"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="最近の Lifelog 一覧を表示（ID確認用）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="出力ディレクトリ（デフォルト: カレントディレクトリ）"
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="音声ファイルを保持する（デフォルト: 削除）"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="ja",
        help="音声の言語（デフォルト: ja）"
    )

    args = parser.parse_args()

    try:
        # クライアント初期化
        print("🚀 Limitless API クライアントを初期化しています...\n")
        client = LimitlessClient()

        # --list オプション: Lifelog 一覧を表示
        if args.list:
            print("=" * 60)
            print("📋 最近の Lifelog 一覧")
            print("=" * 60)
            print()

            result = client.list_lifelogs(limit=10)
            lifelogs = result.get("data", {}).get("lifelogs", [])

            if not lifelogs:
                print("❌ Lifelog が見つかりませんでした。")
                return

            for i, log in enumerate(lifelogs, 1):
                print(f"{i}. ID: {log.get('id')}")
                print(f"   タイトル: {log.get('title')}")
                print(f"   開始: {log.get('startTime')}")
                print(f"   終了: {log.get('endTime')}")
                print()

            print("💡 文字起こしを実行するには:")
            print(f"   python {Path(__file__).name} <lifelog_id>")
            print()
            print("例:")
            if lifelogs:
                first_id = lifelogs[0].get('id')
                print(f"   python {Path(__file__).name} {first_id}")
            return

        # lifelog_id が指定されていない場合
        if not args.lifelog_id:
            print("❌ エラー: Lifelog ID を指定してください。\n")
            print("最近の Lifelog 一覧を確認するには:")
            print(f"   python {Path(__file__).name} --list\n")
            print("文字起こしを実行するには:")
            print(f"   python {Path(__file__).name} <lifelog_id>")
            sys.exit(1)

        # 出力ディレクトリを作成
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("🎤 Lifelog 音声の文字起こしを開始")
        print("=" * 60)
        print()
        print(f"📌 設定:")
        print(f"   Lifelog ID: {args.lifelog_id}")
        print(f"   出力先: {output_dir}")
        print(f"   言語: {args.language}")
        print(f"   音声保持: {'はい' if args.keep_audio else 'いいえ'}")
        print()

        # Lifelog情報を取得して表示
        try:
            lifelog = client.get_lifelog(args.lifelog_id)
            log_data = lifelog.get("data", {})

            print(f"📄 Lifelog 情報:")
            print(f"   タイトル: {log_data.get('title')}")
            print(f"   開始時刻: {log_data.get('startTime')}")
            print(f"   終了時刻: {log_data.get('endTime')}")
            print()
        except Exception as e:
            print(f"⚠️  Lifelog 情報の取得に失敗しました: {e}")
            print()

        # 文字起こし実行
        result = client.transcribe_lifelog(
            lifelog_id=args.lifelog_id,
            output_dir=str(output_dir),
            keep_audio=args.keep_audio,
            language=args.language
        )

        # 結果表示
        print()
        print("=" * 60)
        print("✅ 文字起こし完了！")
        print("=" * 60)
        print()
        print(f"📝 保存されたファイル:")
        print(f"   テキスト: {result['text_file']}")
        print(f"   JSON: {result['json_file']}")
        if result.get('audio_file'):
            print(f"   音声: {result['audio_file']}")
        print()

        # 文字起こしの内容をプレビュー
        transcription_text = result["transcription"]["text"]
        preview_length = 300

        print("📄 文字起こし内容（プレビュー）:")
        print("-" * 60)
        if len(transcription_text) > preview_length:
            print(transcription_text[:preview_length] + "...")
        else:
            print(transcription_text)
        print("-" * 60)
        print()

        # 統計情報
        word_count = len(transcription_text.split())
        char_count = len(transcription_text)
        duration = result["transcription"].get("duration", 0)

        print("📊 統計情報:")
        print(f"   文字数: {char_count:,} 文字")
        print(f"   単語数: {word_count:,} 語")
        if duration:
            print(f"   音声長: {duration:.1f} 秒 ({duration/60:.1f} 分)")
        print()

        print(f"💡 ファイルを確認するには:")
        print(f"   cat {result['text_file']}")
        print(f"   open {result['text_file']}")

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        print()
        print("💡 必要な環境変数を設定してください:")
        print("   export LIMITLESS_API_KEY=\"your_limitless_key\"")
        print("   export OPENAI_API_KEY=\"sk-...\"")
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ API エラー: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
