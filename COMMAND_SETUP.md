# GET_TODO コマンドのセットアップ

## ✅ セットアップ完了

以下のコマンドがターミナルから実行できるようになりました：

- `GET_TODO` - 今日のやるべきことを抽出
- `get-todo` - 同上（小文字版）
- `todo-today` - 同上（別名）

## 🚀 使い方

### 新しいターミナルを開く

```bash
# 新しいターミナルウィンドウまたはタブを開く
# または以下を実行して設定を再読み込み
source ~/.zshrc
```

### コマンドを実行

```bash
# どこからでも実行可能
GET_TODO

# または
get-todo

# または
todo-today

# 直接パス指定でも実行可能
~/bin/GET_TODO
```

## 📋 実行例

```bash
$ GET_TODO

🎯 今日のやるべきことを抽出します

======================================================================
📅 2025-11-22 の Lifelog を取得しています...
======================================================================

✅ 10 件の Lifelog を取得しました

--- 📝 Lifelog 1: ... ---
  💬 明日の予定を決める
  💬 ...

📋 今日の会話から抽出した「やるべきこと」リスト

### 🔴 緊急・直近の予定
1. 明日の予定を決定する
2. 後で連絡する
...

💾 詳細データを daily_todos_2025-11-22.json に保存しました

✅ タスク抽出が完了しました！
```

## 🔧 設定内容

### 1. エイリアス（~/.zshrc に追加済み）

```bash
# Limitless API - TODO 抽出コマンド
alias GET_TODO="python $HOME/limitless-todo-extractor/examples/extract_daily_todos.py"
alias get-todo="python $HOME/limitless-todo-extractor/examples/extract_daily_todos.py"
alias todo-today="python $HOME/limitless-todo-extractor/examples/extract_daily_todos.py"
```

### 2. コマンドスクリプト（~/bin/GET_TODO）

```bash
#!/bin/bash
# Limitless API - 今日のやるべきことを自動抽出

python3 $HOME/limitless-todo-extractor/examples/extract_daily_todos.py "$@"
```

### 3. PATH 設定（~/.zshrc に追加済み）

```bash
# ~/bin を PATH に追加
export PATH="$HOME/bin:$PATH"
```

## 🎯 活用方法

### 毎朝の習慣として

```bash
# ターミナルを開いたら
GET_TODO
```

### cron で自動実行（毎朝8時）

```bash
# crontab を編集
crontab -e

# 以下を追加
0 8 * * * $HOME/bin/GET_TODO > ~/Desktop/today_todos.txt 2>&1
```

### 結果をクリップボードにコピー

```bash
GET_TODO | pbcopy
```

## 🔍 トラブルシューティング

### コマンドが見つからない場合

```bash
# .zshrc を再読み込み
source ~/.zshrc

# PATH を確認
echo $PATH | grep "$HOME/bin"

# コマンドの場所を確認
which GET_TODO
```

### 実行権限がない場合

```bash
chmod +x ~/bin/GET_TODO
```

### API キーが設定されていない場合

```bash
# .zshrc に追加
export LIMITLESS_API_KEY="your_api_key_here"

# 再読み込み
source ~/.zshrc
```

## 📝 その他のコマンド候補

必要に応じて以下のようなコマンドも追加できます：

```bash
# 文字起こしを取得
alias GET_TRANSCRIPT="python $HOME/limitless-todo-extractor/examples/get_transcription.py"

# 日次サマリーを生成
alias DAILY_SUMMARY="python $HOME/limitless-todo-extractor/examples/daily_summary.py"
```

## ✨ まとめ

- **今すぐ使える**: 新しいターミナルで `GET_TODO` を実行
- **自動実行**: cron で毎朝自動実行も可能
- **どこからでも**: カレントディレクトリに関係なく実行可能
