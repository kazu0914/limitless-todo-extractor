# Limitless TODO Extractor

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/kazu0914/limitless-todo-extractor?style=social)](https://github.com/kazu0914/limitless-todo-extractor)

Limitless Pendant の会話記録から「やるべきこと」を自動抽出する Python ツール。

Limitless Developer API を使って、毎日の会話から TODO を AI で自動検出し、ターミナルで `GET_TODO` と入力するだけで即座にタスクリストを表示＆クリップボードにコピーします。

## 特徴

- **クラスベース設計** - 再利用可能で直感的なAPI
- **全エンドポイント対応** - Lifelogs、Audio、Chats の全機能をサポート
- **音声文字起こし** - OpenAI Whisper API による高精度な自動文字起こし
- **レート制限対応** - 自動リトライ機能（180リクエスト/分）
- **ページネーション自動処理** - 大量データを簡単に取得
- **豊富なユーティリティ** - JSON エクスポート、検索、フィルタリング
- **詳細なエラーハンドリング** - わかりやすいエラーメッセージ
- **型ヒント完備** - IDE での自動補完サポート

## インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/kazu0914/limitless-todo-extractor.git
cd limitless-todo-extractor
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成：

```bash
cp .env.example .env
```

`.env` ファイルに API キーを設定：

```bash
LIMITLESS_API_KEY=your_api_key_here
```

または、`.zshrc` / `.bashrc` に直接記載：

```bash
export LIMITLESS_API_KEY="your_api_key_here"
```

## 基本的な使い方

```python
from limitless import LimitlessClient

# クライアントの初期化
client = LimitlessClient()

# 最近のLifelogsを取得
lifelogs = client.list_lifelogs(limit=10)
for log in lifelogs["data"]["lifelogs"]:
    print(f"{log['title']} - {log['startTime']}")
```

## 主な機能

### Lifelogs（ライフログ）

#### 一覧取得

```python
# 今日のLifelogsを取得
today_logs = client.list_lifelogs(date="2025-01-15", limit=10)

# キーワード検索
meeting_logs = client.list_lifelogs(search="会議", limit=5)

# 日付範囲で検索（自動ページネーション）
week_logs = client.search_lifelogs_by_date_range(
    start_date="2025-01-15",
    end_date="2025-01-22",
    search="プロジェクト",
    timezone="Asia/Tokyo"
)
```

#### 個別取得

```python
lifelog = client.get_lifelog("lifelog_id_here")
print(lifelog["data"]["title"])
```

#### 削除

```python
# 注意: この操作は取り消せません
success = client.delete_lifelog("lifelog_id_here")
```

#### JSON エクスポート

```python
client.export_lifelogs_to_json(
    output_path="today_logs.json",
    date="2025-01-15"
)
```

### Audio（音声）

#### 時間範囲指定でダウンロード

```python
# Unix timestamp (ミリ秒) で指定
client.download_audio(
    start_ms=1705305600000,
    end_ms=1705309200000,
    save_path="meeting_audio.ogg"
)
```

#### Lifelog IDから直接ダウンロード

```python
# Lifelogの時間情報を自動的に取得してダウンロード
audio_path = client.download_audio_from_lifelog(
    lifelog_id="lifelog_id_here",
    save_path="my_meeting.ogg"
)
print(f"保存先: {audio_path}")
```

### Chats（チャット）

#### 一覧取得

```python
# 最近のチャットを取得
chats = client.list_chats(limit=20, direction="desc")

# すべてのチャットを取得（自動ページネーション）
all_chats = client.get_all_chats()
```

#### 個別取得

```python
chat = client.get_chat("chat_id_here")
print(chat["data"]["summary"])
```

#### 削除

```python
success = client.delete_chat("chat_id_here")
```

### 文字起こし（Transcription）

**Limitless は録音音声を自動的に文字起こししており、API から無料で取得できます。**

#### 標準機能：Limitless の文字起こし結果を取得（おすすめ・無料）

Limitless は録音した音声を自動的に文字起こしし、以下の情報を生成します：
- **Markdown** - 整形された文字起こし結果
- **Contents** - セグメント化されたテキスト
- **Headings** - 見出し構造
- **Speaker情報** - 話者の識別

```python
# Lifelog を取得（文字起こし済み）
lifelog = client.get_lifelog("lifelog_id_here")
markdown = lifelog["data"]["markdown"]
print(markdown)
```

#### コマンドラインから取得

```bash
# Lifelog 一覧を表示
python examples/get_transcription.py --list

# 文字起こし結果を表示
python examples/get_transcription.py <lifelog_id>

# Markdown形式で保存
python examples/get_transcription.py <lifelog_id> --output ./transcriptions --format markdown
```

#### オプション：OpenAI Whisper で再文字起こし（精度向上が必要な場合のみ）

特定の用途で精度を最大化したい場合、OpenAI Whisper API で再文字起こしできます。

**必要な設定：**

```bash
export OPENAI_API_KEY="sk-..."
```

**使用例：**

```python
# 音声をダウンロードして Whisper で再文字起こし
result = client.transcribe_lifelog("lifelog_id_here")
print(result["transcription"]["text"])
```

**コマンドラインから実行：**

```bash
# Whisper で再文字起こし
python examples/transcribe_lifelog.py <lifelog_id>

# 音声ファイルも保持
python examples/transcribe_lifelog.py <lifelog_id> --keep-audio
```

**料金：**
- Limitless の標準文字起こし：**無料**
- OpenAI Whisper API：$0.006/分（約0.9円/分）

### 今日のやるべきことを自動抽出

**毎日の Lifelog から自動的にタスクを抽出できます。**

実行するだけで、その日（0時00分〜現在時刻）の会話内容を分析し、やるべきことをカテゴリ別に整理して表示します。

**✨ 新機能：** 結果が自動的にクリップボードにコピーされます！

```bash
python examples/extract_daily_todos.py
# または
GET_TODO
```

**出力例：**

```
📋 今日の会話から抽出した「やるべきこと」リスト

### 🔴 緊急・直近の予定
1. 明日の予定を決定する
2. ちゃんとした寿司屋を調べる
3. 後で連絡する

### 🟡 中期的なタスク（今週〜来週）
4. 来週金曜日の予定を確定
5. Excelの勉強を継続する

### 🟢 長期的なタスク
6. 2025年2月のAI資格試験の準備
7. Windowsパソコンの購入を検討

📊 合計: 15 件のタスク候補を検出

======================================================================
✅ タスク抽出が完了しました！
======================================================================
📋 結果をクリップボードにコピーしました
💡 ChatGPT や Claude に貼り付けて要約できます
```

**自動保存：**
- 画面表示と同時にクリップボードにコピー
- `daily_todos_YYYY-MM-DD.json` にも詳細データを保存

**活用方法：**
```bash
# 実行後すぐに ChatGPT や Claude に貼り付け（Cmd+V）
GET_TODO

# AI に以下のように指示して要約
「このタスクリストを優先順位順に整理して、
 今日中にやるべきことをピックアップしてください」
```

## 高度な使い方

### カスタム設定

```python
# レート制限のリトライを無効化
client = LimitlessClient(auto_retry=False)

# 最大リトライ回数を変更
client = LimitlessClient(max_retries=5)

# API キーを直接指定
client = LimitlessClient(api_key="your_api_key")
```

### ページネーション

```python
# 手動でページネーション
cursor = None
all_lifelogs = []

while True:
    result = client.list_lifelogs(limit=10, cursor=cursor)
    data = result["data"]
    all_lifelogs.extend(data["lifelogs"])

    cursor = data.get("nextCursor")
    if not cursor:
        break

print(f"合計 {len(all_lifelogs)} 件取得")
```

### エラーハンドリング

```python
try:
    lifelogs = client.list_lifelogs(date="2025-01-15")
except ValueError as e:
    print(f"設定エラー: {e}")
except RuntimeError as e:
    print(f"APIエラー: {e}")
```

## 使用例

`examples/` ディレクトリに実用的なサンプルコードがあります：

- `basic_usage.py` - 基本的な使い方
- `export_json.py` - データのエクスポート
- `download_audio.py` - 音声ダウンロード
- `daily_summary.py` - 日次レポート生成
- `get_transcription.py` - **文字起こし結果の取得（おすすめ・無料）**
- `transcribe_lifelog.py` - Whisper で再文字起こし（オプション）
- `extract_daily_todos.py` - **今日のやるべきことを自動抽出（NEW!）**

実行例：

```bash
# 基本的な使い方
python examples/basic_usage.py

# JSONエクスポート
python examples/export_json.py --date 2025-01-15

# 文字起こし結果を取得（Limitless標準機能・無料）
python examples/get_transcription.py --list
python examples/get_transcription.py <lifelog_id>

# 今日のやるべきことを自動抽出
python examples/extract_daily_todos.py

# Whisper で再文字起こし（精度向上が必要な場合のみ）
python examples/transcribe_lifelog.py <lifelog_id>
```

## API 制限

- **レート制限**: 180 リクエスト/分（APIキー単位）
- **音声ダウンロード**: 最大2時間（7,200,000ms）
- **Lifelogs取得**: 1リクエストあたり最大10件
- **Chats取得**: 1リクエストあたり最大100件

レート制限に達すると、クライアントは自動的にリトライします（`auto_retry=True` の場合）。

## フォルダ構成

```
limitless-api-client/
├── README.md              # このファイル
├── requirements.txt       # 依存関係
├── .env.example           # 環境変数のテンプレート
├── .gitignore             # Git除外設定
├── limitless/             # メインパッケージ
│   ├── __init__.py
│   └── client.py          # LimitlessClient クラス
├── examples/              # 使用例
│   ├── basic_usage.py
│   ├── export_json.py
│   ├── download_audio.py
│   └── daily_summary.py
└── tests/                 # テストコード
    └── test_client.py
```

## トラブルシューティング

### API キーが設定されていない

```
ValueError: 環境変数 LIMITLESS_API_KEY が設定されていません。
```

**解決方法**: 環境変数を設定してください。

```bash
export LIMITLESS_API_KEY="your_api_key"
```

### レート制限エラー

```
⚠️  レート制限に達しました。60秒後にリトライします...
```

**解決方法**: 自動的にリトライされます。待機時間を短縮したい場合は、リクエスト頻度を下げてください。

### 音声ダウンロードエラー

```
ValueError: ダウンロード時間が最大値（2時間）を超えています。
```

**解決方法**: 時間範囲を2時間以内に分割してください。

## 開発

### テストの実行

```bash
python -m pytest tests/
```

### コードフォーマット

```bash
black limitless/
isort limitless/
```

## ライセンス

MIT License

## 関連リンク

- [Limitless 公式サイト](https://www.limitless.ai/)
- [Limitless Developer Portal](https://www.limitless.ai/developers)
- [API ドキュメント](https://www.limitless.ai/developers)

## サポート

質問や問題がある場合は、Issue を作成してください。
