# Limitless AI と Mac で作る！毎日のタスクを自動抽出する便利コマンドの作り方

## はじめに

日々の会話や打ち合わせの中で「あれ、何をやるって言ったっけ？」と思うことはありませんか？Limitless Pendant は、あなたの会話を常時録音し、AI が自動で文字起こしして記録してくれるウェアラブルデバイスです。

この記事では、Limitless AI の Developer API を使って、今日の会話から「やるべきこと」を自動抽出し、ターミナルで `GET_TODO` と入力するだけで実行できる便利なコマンドを作る方法を解説します。

### この記事で学べること

- Limitless AI / Pendant の基本と Developer API の使い方
- Python で Limitless API クライアントを実装する方法
- Mac のターミナルで使える自作コマンドの作成方法（3通り）
- 実践的なタスク自動抽出システムの構築

### 前提知識

- Python の基本的な知識
- Mac のターミナル操作の基礎
- zsh の基本的な理解

## Limitless AI / Pendant とは

Limitless Pendant は、Limitless 社が開発したウェアラブル型の音声録音デバイスです。首からぶら下げて使用し、周囲の会話を常時録音します。録音された音声はクラウドに自動アップロードされ、AI が以下の処理を行います：

- **高精度な文字起こし**（日本語対応）
- **会話の要約**と見出し生成
- **話者の識別**
- **重要な情報の抽出**

### Developer API の魅力

Limitless は強力な Developer API を提供しており、録音データや文字起こし結果をプログラムから取得できます。これにより、自分だけの便利ツールを作成できます。

**主なエンドポイント：**

- `GET /v1/lifelogs` - ライフログ（会話記録）の一覧取得
- `GET /v1/lifelogs/{id}` - 個別のライフログ取得（文字起こし込み）
- `GET /v1/download-audio` - 音声ファイルのダウンロード
- `GET /v1/chats` - Ask AI チャットの取得

**料金：** 月額45ドル（約6,750円）のプランに加入すると API が利用可能になります。

## Step 1: API キーの取得と環境設定

### 1.1 API キーの取得

1. [Limitless Developer Portal](https://www.limitless.ai/developers) にアクセス
2. ログイン後、API キーを発行
3. 発行されたキーを安全な場所にコピー

### 1.2 環境変数の設定

API キーを環境変数として設定します。`~/.zshrc` を編集しましょう：

```bash
# ~/.zshrc に追加
export LIMITLESS_API_KEY="sk-your-api-key-here"
```

保存後、設定を反映：

```bash
source ~/.zshrc
```

## Step 2: Python API クライアントの実装

まず、Limitless API を扱う Python クライアントを作成します。

### 2.1 プロジェクト構成

```
limitless-api-client/
├── limitless/
│   ├── __init__.py
│   └── client.py
├── examples/
│   └── extract_daily_todos.py
└── requirements.txt
```

### 2.2 基本的な API クライアント

`limitless/client.py` に基本的なクライアントを実装します：

```python
import os
import requests
from typing import Optional, Dict, Any

class LimitlessClient:
    """Limitless Developer API クライアント"""

    BASE_URL = "https://api.limitless.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LIMITLESS_API_KEY")
        if not self.api_key:
            raise ValueError("LIMITLESS_API_KEY が設定されていません")

        self.headers = {"X-API-Key": self.api_key}

    def list_lifelogs(self, date: str, limit: int = 10) -> Dict[str, Any]:
        """指定日の Lifelog を取得"""
        params = {"date": date, "limit": limit}
        response = requests.get(
            f"{self.BASE_URL}/lifelogs",
            headers=self.headers,
            params=params
        )

        if response.status_code != 200:
            raise RuntimeError(f"API Error: {response.text}")

        return response.json()

    def get_lifelog(self, lifelog_id: str) -> Dict[str, Any]:
        """個別の Lifelog を取得（文字起こし込み）"""
        response = requests.get(
            f"{self.BASE_URL}/lifelogs/{lifelog_id}",
            headers=self.headers
        )

        if response.status_code != 200:
            raise RuntimeError(f"API Error: {response.text}")

        return response.json()
```

### 2.3 タスク抽出スクリプトの作成

次に、会話内容からタスクを抽出するスクリプト `examples/extract_daily_todos.py` を作成します：

```python
#!/usr/bin/env python3
from datetime import datetime
from limitless import LimitlessClient

class TodoExtractor:
    # タスクを示唆するキーワード
    TASK_KEYWORDS = [
        'やる', 'する', '予定', '明日', '来週',
        '確認', '準備', '送る', '連絡', '調べる'
    ]

    def __init__(self):
        self.client = LimitlessClient()

    def extract_tasks(self):
        """今日の Lifelog からタスクを抽出"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 今日の Lifelog を取得
        result = self.client.list_lifelogs(date=today, limit=10)
        lifelogs = result.get('data', {}).get('lifelogs', [])

        tasks = []
        for log in lifelogs:
            # 詳細を取得
            detail = self.client.get_lifelog(log['id'])
            contents = detail.get('data', {}).get('lifelog', {}).get('contents', [])

            # 会話からタスクを抽出
            for item in contents:
                if item.get('type') == 'blockquote':
                    text = item.get('content', '')
                    # タスクキーワードを含むか判定
                    if any(keyword in text for keyword in self.TASK_KEYWORDS):
                        tasks.append({
                            'title': log['title'],
                            'content': text
                        })

        return tasks

    def display_tasks(self, tasks):
        """タスクを見やすく表示"""
        print(f"\n📋 今日のやるべきこと ({len(tasks)} 件)\n")

        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task['content'][:80]}")
            print(f"   from: {task['title']}\n")

if __name__ == "__main__":
    extractor = TodoExtractor()
    tasks = extractor.extract_tasks()
    extractor.display_tasks(tasks)
```

## Step 3: Mac でコマンドを作成する方法

Python スクリプトができたら、次はターミナルから簡単に実行できるコマンドを作成します。Mac では主に3つの方法があります。

### 方法1: エイリアスを使う方法（最も簡単）

`~/.zshrc` にエイリアスを追加する方法です。

```bash
# ~/.zshrc に追加
alias GET_TODO="python /path/to/extract_daily_todos.py"
```

**メリット：**
- 設定が簡単
- 即座に使える

**デメリット：**
- `.zshrc` が肥大化する
- 他のユーザーには使えない

### 方法2: ~/bin にスクリプトを配置（おすすめ）

ホームディレクトリに `bin` フォルダを作成し、そこに実行可能なスクリプトを配置する方法です。

**手順：**

```bash
# 1. ~/bin ディレクトリを作成
mkdir -p ~/bin

# 2. ラッパースクリプトを作成
cat > ~/bin/GET_TODO << 'EOF'
#!/bin/bash
python3 /path/to/extract_daily_todos.py "$@"
EOF

# 3. 実行権限を付与
chmod +x ~/bin/GET_TODO

# 4. PATH に追加（~/.zshrc に記述）
export PATH="$HOME/bin:$PATH"

# 5. 設定を反映
source ~/.zshrc
```

**メリット：**
- 整理されている
- スクリプトの管理がしやすい
- 複数のコマンドを管理できる

**デメリット：**
- 初回設定が少し複雑

### 方法3: シンボリックリンクを使う方法

`/usr/local/bin` にシンボリックリンクを作成する方法です。

```bash
# シンボリックリンクを作成
sudo ln -s /path/to/extract_daily_todos.py /usr/local/bin/get-todo

# 実行権限を確認
chmod +x /path/to/extract_daily_todos.py
```

**メリット：**
- システム全体で使える
- 他のユーザーも使える

**デメリット：**
- sudo 権限が必要
- システムディレクトリを触るため慎重に

## Step 4: 実践 - GET_TODO コマンドの作成

では、実際に今回作成したスクリプトをコマンド化しましょう。おすすめの方法2（~/bin を使う方法）で進めます。

### 4.1 ディレクトリ作成とスクリプト配置

```bash
# ~/bin を作成
mkdir -p ~/bin

# ラッパースクリプトを作成
cat > ~/bin/GET_TODO << 'EOF'
#!/bin/bash
# Limitless API - 今日のやるべきことを自動抽出

python3 /Users/$(whoami)/claude_code/limitless-api-client/examples/extract_daily_todos.py "$@"
EOF

# 実行権限を付与
chmod +x ~/bin/GET_TODO
```

### 4.2 PATH の設定

`~/.zshrc` を編集して、`~/bin` を PATH に追加します：

```bash
# ~/.zshrc の末尾に追加
export PATH="$HOME/bin:$PATH"
```

### 4.3 エイリアスも追加（オプション）

より使いやすくするため、複数のエイリアスを追加します：

```bash
# ~/.zshrc に追加
alias GET_TODO="python /path/to/extract_daily_todos.py"
alias get-todo="python /path/to/extract_daily_todos.py"
alias todo-today="python /path/to/extract_daily_todos.py"
```

### 4.4 設定の反映と動作確認

```bash
# 設定を反映
source ~/.zshrc

# コマンドが認識されているか確認
which GET_TODO
# 出力: /Users/username/bin/GET_TODO

# 実行
GET_TODO
```

## Step 5: 活用方法

### 毎朝の習慣に

```bash
# ターミナルを開いたら
GET_TODO
```

### cron で自動実行

毎朝8時に自動実行して、デスクトップにファイルとして保存：

```bash
# crontab を編集
crontab -e

# 以下を追加
0 8 * * * /Users/$(whoami)/bin/GET_TODO > ~/Desktop/today_todos.txt 2>&1
```

### 結果をクリップボードにコピー

```bash
GET_TODO | pbcopy
```

### Slack や Notion に自動投稿

スクリプトを拡張して、抽出したタスクを Slack や Notion に自動投稿することも可能です。

## トラブルシューティング

### コマンドが見つからない

```bash
# PATH を確認
echo $PATH | grep "$HOME/bin"

# .zshrc を再読み込み
source ~/.zshrc
```

### 実行権限がない

```bash
chmod +x ~/bin/GET_TODO
```

### API エラー

```bash
# API キーを確認
echo $LIMITLESS_API_KEY

# 環境変数を再設定
export LIMITLESS_API_KEY="your-key"
source ~/.zshrc
```

## まとめ

この記事では、Limitless AI の Developer API を使って、日々の会話から「やるべきこと」を自動抽出し、Mac のターミナルで簡単に実行できるコマンドを作成する方法を解説しました。

**重要なポイント：**

1. **Limitless API** は録音データと文字起こし結果にプログラムからアクセスできる
2. **Python クライアント**で API を簡単に扱える
3. **Mac のコマンド作成**は主に3つの方法がある
   - エイリアス（簡単）
   - ~/bin に配置（おすすめ）
   - シンボリックリンク（システム全体で使える）
4. **自動化**により、毎日のタスク管理が劇的に効率化

このアプローチを応用すれば、議事録の自動生成、重要な会話の抽出、定期レポートの作成など、様々な便利ツールを作成できます。

ぜひ、あなた自身の業務に合わせてカスタマイズしてみてください！

---

**関連リンク：**

- [Limitless Developer Portal](https://www.limitless.ai/developers)
- [GitHub - サンプルコード](https://github.com/anthropics/limitless-api-client)

**文字数：約 4,850 文字**
