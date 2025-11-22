#!/usr/bin/env python3
"""
Lifelog の音声をダウンロードするサンプル

実行方法:
    python examples/download_audio.py <lifelog_id>
    python examples/download_audio.py <lifelog_id> --output my_audio.ogg
"""

import sys
import argparse
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def main():
    """Lifelog の音声をダウンロード"""

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Limitless Lifelog の音声を Ogg Opus 形式でダウンロード"
    )
    parser.add_argument(
        "lifelog_id",
        type=str,
        nargs="?",
        help="ダウンロードする Lifelog の ID"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="出力ファイルパス。未指定時は自動生成されます。"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="最近の Lifelog 一覧を表示（ID確認用）"
    )

    args = parser.parse_args()

    try:
        # クライアント初期化
        client = LimitlessClient()

        # --list オプション: Lifelog 一覧を表示
        if args.list:
            print("📋 最近の Lifelog 一覧:\n")
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

            print("💡 音声をダウンロードするには:")
            print(f"   python {Path(__file__).name} <lifelog_id>")
            return

        # lifelog_id が指定されていない場合
        if not args.lifelog_id:
            print("❌ エラー: Lifelog ID を指定してください。\n")
            print("最近の Lifelog 一覧を確認するには:")
            print(f"   python {Path(__file__).name} --list\n")
            print("音声をダウンロードするには:")
            print(f"   python {Path(__file__).name} <lifelog_id>")
            sys.exit(1)

        # 音声ダウンロード
        print(f"🎵 Lifelog の音声をダウンロードしています...")
        print(f"   Lifelog ID: {args.lifelog_id}\n")

        # Lifelog情報を取得して表示
        lifelog = client.get_lifelog(args.lifelog_id)
        log_data = lifelog.get("data", {})

        print(f"📄 Lifelog 情報:")
        print(f"   タイトル: {log_data.get('title')}")
        print(f"   開始時刻: {log_data.get('startTime')}")
        print(f"   終了時刻: {log_data.get('endTime')}")
        print()

        # 音声ダウンロード実行
        audio_path = client.download_audio_from_lifelog(
            lifelog_id=args.lifelog_id,
            save_path=args.output
        )

        print(f"✅ ダウンロード完了: {audio_path}")

        # ファイルサイズを表示
        file_size = Path(audio_path).stat().st_size
        print(f"   ファイルサイズ: {file_size / 1024 / 1024:.2f} MB")

        print(f"\n💡 再生方法:")
        print(f"   vlc {audio_path}")
        print(f"   ffplay {audio_path}")

    except ValueError as e:
        print(f"❌ エラー: {e}")
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
