#!/usr/bin/env python3
"""
今日の Lifelog からやるべきことを抽出するスクリプト

実行するとその日（0時00分〜現在時刻）の会話内容を分析し、
タスクや予定を自動抽出してリスト化します。

実行方法:
    python examples/extract_daily_todos.py

    または実行権限を付与して:
    chmod +x examples/extract_daily_todos.py
    ./examples/extract_daily_todos.py
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from io import StringIO
import json
import re

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from limitless import LimitlessClient


class TodoExtractor:
    """Lifelog からタスクを抽出するクラス"""

    # タスクを示唆するキーワード
    TASK_KEYWORDS = [
        'やる', 'する', 'しなければ', 'しないと', 'やらなきゃ',
        '予定', '明日', '来週', 'TODO', 'タスク', '確認',
        '準備', '送る', '連絡', '調べる', '買う', '行く',
        'どうする', '決める', 'やること', '後で', '今度',
        '来る', '会う', '食べる', 'あげる', '渡す'
    ]

    # 緊急性の高いキーワード
    URGENT_KEYWORDS = ['明日', '今日', '今から', '後で', 'すぐ']

    # 中期的なキーワード
    MEDIUM_KEYWORDS = ['来週', '今週', '金曜', '土曜', '日曜']

    # 長期的なキーワード
    LONG_KEYWORDS = ['来月', '来年', '2月', '資格', '試験']

    def __init__(self):
        self.client = LimitlessClient()

    def get_todays_lifelogs(self):
        """今日の Lifelog を取得"""
        today = datetime.now().strftime("%Y-%m-%d")

        print('=' * 70)
        print(f'📅 {today} の Lifelog を取得しています...')
        print('=' * 70)
        print()

        result = self.client.list_lifelogs(date=today, limit=10)
        lifelogs = result.get('data', {}).get('lifelogs', [])

        print(f'✅ {len(lifelogs)} 件の Lifelog を取得しました\n')

        return lifelogs, today

    def extract_conversations(self, lifelogs):
        """Lifelog から会話内容を抽出"""
        all_conversations = []

        for i, log in enumerate(lifelogs, 1):
            log_id = log.get('id')
            title = log.get('title')
            start_time = log.get('startTime')

            # 詳細を取得
            detail = self.client.get_lifelog(log_id)
            log_data = detail.get('data', {}).get('lifelog', {})
            contents = log_data.get('contents', [])

            if not contents:
                continue

            print(f'\n--- 📝 Lifelog {i}: {title} ({start_time[:16]}) ---\n')

            # 会話内容を抽出
            conversation_text = []
            for item in contents:
                if item.get('type') == 'blockquote':
                    content = item.get('content', '')
                    conversation_text.append(content)
                    # 最初の3つだけプレビュー表示
                    if len(conversation_text) <= 3:
                        print(f'  💬 {content[:100]}')

            if len(conversation_text) > 3:
                print(f'  💬 ... （他 {len(conversation_text) - 3} 件）')

            all_conversations.append({
                'id': log_id,
                'title': title,
                'time': start_time,
                'conversation': conversation_text
            })

        return all_conversations

    def categorize_task(self, text):
        """タスクの緊急性を判定"""
        text_lower = text

        for keyword in self.URGENT_KEYWORDS:
            if keyword in text_lower:
                return 'urgent'

        for keyword in self.MEDIUM_KEYWORDS:
            if keyword in text_lower:
                return 'medium'

        for keyword in self.LONG_KEYWORDS:
            if keyword in text_lower:
                return 'long'

        return 'other'

    def extract_tasks(self, conversations):
        """会話内容からタスクを抽出"""
        tasks = {
            'urgent': [],    # 緊急・直近
            'medium': [],    # 中期的
            'long': [],      # 長期的
            'other': []      # その他
        }

        for conv in conversations:
            title = conv['title']
            time = conv['time']

            for text in conv['conversation']:
                # タスクキーワードを含むか判定
                is_task = False
                for keyword in self.TASK_KEYWORDS:
                    if keyword in text:
                        is_task = True
                        break

                if is_task:
                    category = self.categorize_task(text)
                    tasks[category].append({
                        'time': time,
                        'title': title,
                        'content': text
                    })

        return tasks

    def display_tasks(self, tasks):
        """タスクを見やすく表示"""
        print('\n' + '=' * 70)
        print('📋 今日の会話から抽出した「やるべきこと」リスト')
        print('=' * 70)
        print()

        # 緊急タスク
        if tasks['urgent']:
            print('### 🔴 緊急・直近の予定\n')
            for i, task in enumerate(tasks['urgent'], 1):
                print(f"{i}. {task['content'][:100]}")
                print(f"   ⏰ {task['time'][:16]} | 📁 {task['title']}")
                print()

        # 中期的タスク
        if tasks['medium']:
            print('### 🟡 中期的なタスク（今週〜来週）\n')
            for i, task in enumerate(tasks['medium'], 1):
                print(f"{i}. {task['content'][:100]}")
                print(f"   ⏰ {task['time'][:16]} | 📁 {task['title']}")
                print()

        # 長期的タスク
        if tasks['long']:
            print('### 🟢 長期的なタスク\n')
            for i, task in enumerate(tasks['long'], 1):
                print(f"{i}. {task['content'][:100]}")
                print(f"   ⏰ {task['time'][:16]} | 📁 {task['title']}")
                print()

        # その他
        if tasks['other']:
            print('### ⚪️ その他のタスク候補\n')
            # 最大10件まで表示
            for i, task in enumerate(tasks['other'][:10], 1):
                print(f"{i}. {task['content'][:100]}")
                print(f"   ⏰ {task['time'][:16]} | 📁 {task['title']}")
                print()

            if len(tasks['other']) > 10:
                print(f"   ... （他 {len(tasks['other']) - 10} 件）\n")

        # 統計情報
        total = sum(len(tasks[cat]) for cat in tasks)
        print('---')
        print(f'📊 合計: {total} 件のタスク候補を検出')
        print(f'   🔴 緊急: {len(tasks["urgent"])} 件')
        print(f'   🟡 中期: {len(tasks["medium"])} 件')
        print(f'   🟢 長期: {len(tasks["long"])} 件')
        print(f'   ⚪️ その他: {len(tasks["other"])} 件')
        print()

    def save_results(self, conversations, tasks, today):
        """結果を JSON ファイルに保存"""
        output_data = {
            'date': today,
            'extracted_at': datetime.now().isoformat(),
            'total_conversations': len(conversations),
            'tasks': tasks,
            'conversations': conversations
        }

        output_file = f'daily_todos_{today}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f'💾 詳細データを {output_file} に保存しました')
        print()

    def copy_to_clipboard(self, text):
        """テキストをクリップボードにコピー"""
        try:
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'))
            return True
        except Exception as e:
            print(f'⚠️  クリップボードへのコピーに失敗しました: {e}')
            return False

    def run(self):
        """メイン処理"""
        # 出力を保存するバッファ
        output_buffer = StringIO()

        try:
            # 1. 今日の Lifelog を取得
            lifelogs, today = self.get_todays_lifelogs()

            if not lifelogs:
                msg = '❌ 今日の Lifelog が見つかりませんでした。'
                print(msg)
                output_buffer.write(msg + '\n')
                return

            # 2. 会話内容を抽出
            conversations = self.extract_conversations(lifelogs)

            if not conversations:
                msg = '❌ 会話内容が取得できませんでした。'
                print(msg)
                output_buffer.write(msg + '\n')
                return

            # 3. タスクを抽出
            tasks = self.extract_tasks(conversations)

            # 4. タスクを表示（出力をバッファにも保存）
            original_stdout = sys.stdout

            # タスク表示部分の出力をキャプチャ
            output_buffer.write('\n' + '=' * 70 + '\n')
            output_buffer.write('📋 今日の会話から抽出した「やるべきこと」リスト\n')
            output_buffer.write('=' * 70 + '\n\n')

            # 緊急タスク
            if tasks['urgent']:
                section = '### 🔴 緊急・直近の予定\n\n'
                output_buffer.write(section)
                for i, task in enumerate(tasks['urgent'], 1):
                    line = f"{i}. {task['content'][:100]}\n"
                    output_buffer.write(line)
                output_buffer.write('\n')

            # 中期的タスク
            if tasks['medium']:
                section = '### 🟡 中期的なタスク（今週〜来週）\n\n'
                output_buffer.write(section)
                for i, task in enumerate(tasks['medium'], 1):
                    line = f"{i}. {task['content'][:100]}\n"
                    output_buffer.write(line)
                output_buffer.write('\n')

            # 長期的タスク
            if tasks['long']:
                section = '### 🟢 長期的なタスク\n\n'
                output_buffer.write(section)
                for i, task in enumerate(tasks['long'], 1):
                    line = f"{i}. {task['content'][:100]}\n"
                    output_buffer.write(line)
                output_buffer.write('\n')

            # その他
            if tasks['other']:
                section = '### ⚪️ その他のタスク候補\n\n'
                output_buffer.write(section)
                for i, task in enumerate(tasks['other'][:10], 1):
                    line = f"{i}. {task['content'][:100]}\n"
                    output_buffer.write(line)
                if len(tasks['other']) > 10:
                    output_buffer.write(f"\n（他 {len(tasks['other']) - 10} 件）\n")
                output_buffer.write('\n')

            # 統計情報
            total = sum(len(tasks[cat]) for cat in tasks)
            output_buffer.write('---\n')
            output_buffer.write(f'📊 合計: {total} 件のタスク候補を検出\n')
            output_buffer.write(f'   🔴 緊急: {len(tasks["urgent"])} 件\n')
            output_buffer.write(f'   🟡 中期: {len(tasks["medium"])} 件\n')
            output_buffer.write(f'   🟢 長期: {len(tasks["long"])} 件\n')
            output_buffer.write(f'   ⚪️ その他: {len(tasks["other"])} 件\n')

            # 画面に表示
            self.display_tasks(tasks)

            # 5. 結果を保存
            self.save_results(conversations, tasks, today)

            print('=' * 70)
            print('✅ タスク抽出が完了しました！')
            print('=' * 70)

            # 6. クリップボードにコピー
            clipboard_content = output_buffer.getvalue()
            if self.copy_to_clipboard(clipboard_content):
                print('📋 結果をクリップボードにコピーしました')
                print('💡 ChatGPT や Claude に貼り付けて要約できます')

            print()

        except ValueError as e:
            print(f'❌ 設定エラー: {e}')
            print()
            print('💡 環境変数 LIMITLESS_API_KEY を設定してください:')
            print('   export LIMITLESS_API_KEY="your_api_key"')
            sys.exit(1)

        except RuntimeError as e:
            print(f'❌ API エラー: {e}')
            sys.exit(1)

        except Exception as e:
            print(f'❌ 予期しないエラー: {e}')
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """エントリーポイント"""
    print()
    print('🎯 今日のやるべきことを抽出します')
    print()

    extractor = TodoExtractor()
    extractor.run()


if __name__ == "__main__":
    main()
