#!/usr/bin/env python3
"""
基本的な使い方のサンプル

実行方法:
    python examples/basic_usage.py
"""

import sys
from pathlib import Path

# 親ディレクトリをパスに追加（パッケージをインポートできるようにする）
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


def main():
    """基本的な使い方のデモンストレーション"""

    try:
        # クライアントの初期化
        print("🚀 Limitless API クライアントを初期化しています...\n")
        client = LimitlessClient()

        # ---------------------------------------------------
        # 1. Lifelogs の取得
        # ---------------------------------------------------
        print("=" * 60)
        print("📋 最近の Lifelogs を取得")
        print("=" * 60)

        lifelogs_result = client.list_lifelogs(limit=5)
        lifelogs = lifelogs_result.get("data", {}).get("lifelogs", [])

        if not lifelogs:
            print("❌ Lifelogs が見つかりませんでした。")
        else:
            print(f"\n✅ {len(lifelogs)} 件の Lifelog を取得しました:\n")
            for i, log in enumerate(lifelogs, 1):
                print(f"{i}. {log.get('title')}")
                print(f"   開始: {log.get('startTime')}")
                print(f"   終了: {log.get('endTime')}")
                print(f"   スター: {'⭐️' if log.get('isStarred') else '☆'}")
                print()

        # ---------------------------------------------------
        # 2. キーワード検索
        # ---------------------------------------------------
        print("=" * 60)
        print("🔍 キーワード検索（'meeting' または '会議'）")
        print("=" * 60)

        search_result = client.list_lifelogs(search="meeting", limit=3)
        search_logs = search_result.get("data", {}).get("lifelogs", [])

        if not search_logs:
            print("❌ 該当する Lifelog が見つかりませんでした。")
        else:
            print(f"\n✅ {len(search_logs)} 件の検索結果:\n")
            for log in search_logs:
                print(f"- {log.get('title')}")

        # ---------------------------------------------------
        # 3. Chats の取得
        # ---------------------------------------------------
        print("\n" + "=" * 60)
        print("💬 最近のチャットを取得")
        print("=" * 60)

        chats_result = client.list_chats(limit=3)
        chats = chats_result.get("data", {}).get("chats", [])

        if not chats:
            print("❌ チャットが見つかりませんでした。")
        else:
            print(f"\n✅ {len(chats)} 件のチャットを取得しました:\n")
            for i, chat in enumerate(chats, 1):
                print(f"{i}. ID: {chat.get('id')}")
                print(f"   要約: {chat.get('summary', 'N/A')[:80]}...")
                print(f"   作成: {chat.get('createdAt')}")
                print()

        # ---------------------------------------------------
        # 4. 個別の Lifelog 取得（最初のものを使用）
        # ---------------------------------------------------
        if lifelogs:
            print("=" * 60)
            print("📄 個別の Lifelog を詳細取得")
            print("=" * 60)

            first_log_id = lifelogs[0].get("id")
            detail = client.get_lifelog(first_log_id)

            log_data = detail.get("data", {})
            print(f"\n✅ Lifelog詳細:")
            print(f"   ID: {log_data.get('id')}")
            print(f"   タイトル: {log_data.get('title')}")
            print(f"   開始: {log_data.get('startTime')}")
            print(f"   終了: {log_data.get('endTime')}")

        print("\n" + "=" * 60)
        print("✅ すべての処理が正常に完了しました！")
        print("=" * 60)

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        print("\n💡 ヒント: 環境変数 LIMITLESS_API_KEY が設定されているか確認してください。")
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ API エラー: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
