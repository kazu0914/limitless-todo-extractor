#!/usr/bin/env python3
"""
Lifelogsを JSON ファイルにエクスポートするサンプル

実行方法:
    python examples/export_json.py
    python examples/export_json.py --date 2025-01-15
    python examples/export_json.py --search "会議"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def main():
    """Lifelogs を JSON ファイルにエクスポート"""

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Limitless Lifelogs を JSON 形式でエクスポート"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="日付フィルタ（YYYY-MM-DD形式）。例: 2025-01-15"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="検索キーワード。例: 会議"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="出力ファイルパス。未指定時は自動生成されます。"
    )

    args = parser.parse_args()

    try:
        # クライアント初期化
        client = LimitlessClient()

        # 出力ファイル名を決定
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.date:
                output_path = f"lifelogs_{args.date}.json"
            elif args.search:
                output_path = f"lifelogs_search_{timestamp}.json"
            else:
                output_path = f"lifelogs_{timestamp}.json"

        # エクスポート実行
        print("📥 Lifelogs をエクスポートしています...")
        print(f"   日付フィルタ: {args.date or 'なし'}")
        print(f"   検索キーワード: {args.search or 'なし'}")
        print(f"   出力先: {output_path}\n")

        saved_path = client.export_lifelogs_to_json(
            output_path=output_path,
            date=args.date,
            search=args.search
        )

        print(f"✅ エクスポート完了: {saved_path}")

        # ファイルサイズを表示
        file_size = Path(saved_path).stat().st_size
        print(f"   ファイルサイズ: {file_size:,} bytes")

        # 取得件数を表示（JSONを読み込んで確認）
        import json
        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            count = len(data.get("data", {}).get("lifelogs", []))
            print(f"   Lifelog 件数: {count} 件")

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ API エラー: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
