#!/usr/bin/env python3
"""
Limitless Lifelog の文字起こし結果を取得するサンプル

Limitless は録音音声を自動的に文字起こししており、
API から直接文字起こし済みのテキストを取得できます。

実行方法:
    # Lifelog 一覧を表示
    python examples/get_transcription.py --list

    # 特定の Lifelog の文字起こしを取得
    python examples/get_transcription.py <lifelog_id>

    # Markdown形式で保存
    python examples/get_transcription.py <lifelog_id> --output ./transcriptions
"""

import sys
import argparse
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def main():
    """Lifelog の文字起こし結果を取得"""

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Limitless Lifelog の文字起こし結果を取得（無料・Limitless標準機能）"
    )
    parser.add_argument(
        "lifelog_id",
        type=str,
        nargs="?",
        help="取得する Lifelog の ID"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="最近の Lifelog 一覧を表示（ID確認用）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="出力ディレクトリ（指定時はファイルに保存）"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "markdown", "json"],
        default="text",
        help="出力形式（デフォルト: text）"
    )

    args = parser.parse_args()

    try:
        # クライアント初期化
        client = LimitlessClient()

        # --list オプション: Lifelog 一覧を表示
        if args.list:
            print("=" * 60)
            print("📋 最近の Lifelog 一覧（文字起こし済み）")
            print("=" * 60)
            print()

            result = client.list_lifelogs(limit=10, include_contents=True)
            lifelogs = result.get("data", {}).get("lifelogs", [])

            if not lifelogs:
                print("❌ Lifelog が見つかりませんでした。")
                return

            for i, log in enumerate(lifelogs, 1):
                print(f"{i}. ID: {log.get('id')}")
                print(f"   タイトル: {log.get('title')}")
                print(f"   開始: {log.get('startTime')}")

                # プレビュー表示
                markdown = log.get('markdown', '')
                if markdown:
                    preview = markdown[:100].replace('\n', ' ')
                    print(f"   内容: {preview}...")

                print()

            print("💡 文字起こしを取得するには:")
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
            print("文字起こしを取得するには:")
            print(f"   python {Path(__file__).name} <lifelog_id>")
            sys.exit(1)

        print("=" * 60)
        print("📄 Lifelog の文字起こし結果を取得")
        print("=" * 60)
        print()

        # Lifelog を取得（文字起こし込み）
        lifelog_result = client.get_lifelog(args.lifelog_id)
        log_data = lifelog_result.get("data", {})

        # 基本情報を表示
        print(f"📌 Lifelog 情報:")
        print(f"   ID: {log_data.get('id')}")
        print(f"   タイトル: {log_data.get('title')}")
        print(f"   開始時刻: {log_data.get('startTime')}")
        print(f"   終了時刻: {log_data.get('endTime')}")
        print()

        # 文字起こし結果を取得
        markdown = log_data.get('markdown', '')
        contents = log_data.get('contents', '')

        if not markdown and not contents:
            print("❌ この Lifelog には文字起こし結果が含まれていません。")
            return

        # 出力形式に応じて処理
        if args.output:
            # ディレクトリ作成
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            # ファイル保存
            if args.format == "markdown":
                output_file = output_dir / f"lifelog_{args.lifelog_id}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"# {log_data.get('title')}\n\n")
                    f.write(f"**開始**: {log_data.get('startTime')}\n")
                    f.write(f"**終了**: {log_data.get('endTime')}\n\n")
                    f.write("---\n\n")
                    f.write(markdown)

            elif args.format == "json":
                import json
                output_file = output_dir / f"lifelog_{args.lifelog_id}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)

            else:  # text
                output_file = output_dir / f"lifelog_{args.lifelog_id}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(contents or markdown)

            print(f"✅ 保存完了: {output_file}")
            print()

        # プレビュー表示
        print("📄 文字起こし内容:")
        print("=" * 60)

        display_text = markdown if markdown else contents
        preview_length = 500

        if len(display_text) > preview_length:
            print(display_text[:preview_length])
            print("\n...")
            print(f"\n（残り {len(display_text) - preview_length} 文字）")
        else:
            print(display_text)

        print("=" * 60)
        print()

        # 統計情報
        char_count = len(display_text)
        word_count = len(display_text.split())

        print("📊 統計情報:")
        print(f"   文字数: {char_count:,} 文字")
        print(f"   単語数: {word_count:,} 語")
        print()

        if not args.output:
            print("💡 ファイルに保存するには:")
            print(f"   python {Path(__file__).name} {args.lifelog_id} --output ./transcriptions")

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
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
