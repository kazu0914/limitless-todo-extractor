#!/usr/bin/env python3
"""
日次サマリーレポートを生成するサンプル

実行方法:
    python examples/daily_summary.py
    python examples/daily_summary.py --date 2025-01-15
    python examples/daily_summary.py --date 2025-01-15 --output report.md
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def format_duration(start_time: str, end_time: str) -> str:
    """開始時刻と終了時刻から所要時間を計算"""
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration = end - start

        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60

        if hours > 0:
            return f"{hours}時間{minutes}分"
        else:
            return f"{minutes}分"
    except:
        return "不明"


def generate_markdown_report(date: str, lifelogs: list) -> str:
    """Markdown形式のレポートを生成"""

    report = f"# 📅 {date} の活動サマリー\n\n"
    report += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "---\n\n"

    if not lifelogs:
        report += "❌ この日の Lifelog は見つかりませんでした。\n"
        return report

    # 統計情報
    report += "## 📊 統計情報\n\n"
    report += f"- **総活動数**: {len(lifelogs)} 件\n"

    starred_count = sum(1 for log in lifelogs if log.get("isStarred"))
    report += f"- **スター付き**: {starred_count} 件\n"

    # 総時間を計算
    total_minutes = 0
    for log in lifelogs:
        start_time = log.get("startTime")
        end_time = log.get("endTime")
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration = end - start
                total_minutes += duration.seconds // 60
            except:
                pass

    total_hours = total_minutes // 60
    total_mins = total_minutes % 60
    report += f"- **総記録時間**: {total_hours}時間{total_mins}分\n\n"

    # 活動一覧
    report += "## 📋 活動一覧\n\n"

    for i, log in enumerate(lifelogs, 1):
        title = log.get("title", "無題")
        start_time = log.get("startTime", "")
        end_time = log.get("endTime", "")
        is_starred = log.get("isStarred", False)

        # 時刻のフォーマット
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            start_str = start_dt.strftime("%H:%M")
        except:
            start_str = "不明"

        try:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            end_str = end_dt.strftime("%H:%M")
        except:
            end_str = "不明"

        duration = format_duration(start_time, end_time)
        star_mark = "⭐️ " if is_starred else ""

        report += f"### {i}. {star_mark}{title}\n\n"
        report += f"- **時間**: {start_str} - {end_str} ({duration})\n"
        report += f"- **ID**: `{log.get('id')}`\n"

        # コンテンツがあれば表示
        if "contents" in log and log["contents"]:
            content = log["contents"][:200]
            report += f"- **内容**: {content}...\n"

        report += "\n"

    # フッター
    report += "---\n\n"
    report += "_このレポートは Limitless API Client によって自動生成されました。_\n"

    return report


def main():
    """日次サマリーレポートを生成"""

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Limitless Lifelogs の日次サマリーレポートを生成"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="レポート対象日（YYYY-MM-DD形式）。未指定時は今日。"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="出力ファイルパス。未指定時は標準出力。"
    )

    args = parser.parse_args()

    try:
        # クライアント初期化
        client = LimitlessClient()

        # 日付を決定
        if args.date:
            target_date = args.date
        else:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # Lifelogs を取得
        print(f"📥 {target_date} の Lifelogs を取得しています...\n")

        result = client.list_lifelogs(
            date=target_date,
            limit=10,
            include_contents=True
        )

        lifelogs = result.get("data", {}).get("lifelogs", [])

        # レポート生成
        print(f"📝 レポートを生成しています...\n")
        report = generate_markdown_report(target_date, lifelogs)

        # 出力
        if args.output:
            # ファイルに保存
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ レポート保存完了: {args.output}")
        else:
            # 標準出力
            print(report)

        print(f"\n✅ サマリー生成完了！")
        print(f"   対象日: {target_date}")
        print(f"   活動数: {len(lifelogs)} 件")

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ API エラー: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
