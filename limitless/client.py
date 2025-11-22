import os
import json
import time
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class LimitlessClient:
    """
    Limitless Developer API を扱うためのクライアントクラス

    主な機能:
    - Lifelogs の取得・削除・検索
    - Audio のダウンロード
    - Chats の取得・削除
    - レート制限への自動対応（リトライ機能）
    """

    BASE_URL = "https://api.limitless.ai/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        auto_retry: bool = True,
        max_retries: int = 3
    ):
        """
        クライアントの初期化処理

        引数:
            api_key (str | None): APIキー。未指定時は環境変数 LIMITLESS_API_KEY から読み込む
            auto_retry (bool): レート制限時に自動リトライするか（デフォルト: True）
            max_retries (int): 最大リトライ回数（デフォルト: 3）

        例外:
            ValueError: APIキーが設定されていない場合
        """
        self.api_key = api_key or os.environ.get("LIMITLESS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "環境変数 LIMITLESS_API_KEY が設定されていません。\n"
                ".zshrc に以下を追加してください:\n"
                "  export LIMITLESS_API_KEY=\"xxxxx\""
            )

        self.headers = {"X-API-Key": self.api_key}
        self.auto_retry = auto_retry
        self.max_retries = max_retries

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        HTTPリクエストを実行する内部メソッド（レート制限対応）

        引数:
            method (str): HTTPメソッド（GET, POST, DELETE など）
            endpoint (str): エンドポイントパス
            params (dict | None): クエリパラメータ
            **kwargs: requests に渡す追加引数

        戻り値:
            requests.Response: レスポンスオブジェクト

        例外:
            RuntimeError: リクエストが失敗した場合
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
                **kwargs
            )

            # 成功時
            if response.status_code == 200:
                return response

            # レート制限時
            if response.status_code == 429 and self.auto_retry:
                try:
                    error_data = response.json()
                    retry_after = int(error_data.get("retryAfter", 60))
                except:
                    retry_after = 60

                if attempt < self.max_retries - 1:
                    print(f"⚠️  レート制限に達しました。{retry_after}秒後にリトライします...")
                    time.sleep(retry_after)
                    continue

            # その他のエラー
            raise RuntimeError(
                f"APIリクエストに失敗しました。\n"
                f"  URL: {url}\n"
                f"  Status: {response.status_code}\n"
                f"  Body: {response.text}"
            )

        raise RuntimeError(f"最大リトライ回数（{self.max_retries}）を超えました。")

    # ---------------------------------------------------
    # Lifelogs（ライフログ）
    # ---------------------------------------------------

    def list_lifelogs(
        self,
        limit: int = 10,
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        timezone: Optional[str] = None,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        include_contents: bool = False
    ) -> Dict[str, Any]:
        """
        Lifelog の一覧取得

        引数:
            limit (int): 取得件数（最大10、デフォルト10）
            date (str | None): 日付フィルタ "YYYY-MM-DD" 形式
            start (str | None): 開始日時（ISO 8601形式）
            end (str | None): 終了日時（ISO 8601形式）
            timezone (str | None): タイムゾーン（例: "America/New_York"）
            search (str | None): 検索クエリ
            cursor (str | None): ページネーション用カーソル
            include_contents (bool): コンテンツを含めるか（デフォルト: False）

        戻り値:
            dict: APIレスポンス（lifelogs配列とメタデータを含む）

        使用例:
            # 今日のLifelogsを取得
            client.list_lifelogs(date="2025-01-15", limit=10)

            # キーワード検索
            client.list_lifelogs(search="会議", limit=5)
        """
        params = {
            "limit": min(limit, 10),  # 最大10に制限
            "includeContents": str(include_contents).lower()
        }

        if date:
            params["date"] = date
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if timezone:
            params["timezone"] = timezone
        if search:
            params["search"] = search
        if cursor:
            params["cursor"] = cursor

        response = self._request("GET", "/lifelogs", params=params)
        return response.json()

    def get_lifelog(self, lifelog_id: str) -> Dict[str, Any]:
        """
        特定のLifelogを取得

        引数:
            lifelog_id (str): Lifelog ID

        戻り値:
            dict: Lifelogデータ
        """
        response = self._request("GET", f"/lifelogs/{lifelog_id}")
        return response.json()

    def delete_lifelog(self, lifelog_id: str) -> bool:
        """
        Lifelogを削除（関連する音声・トランスクリプト・メタデータも削除）

        引数:
            lifelog_id (str): 削除するLifelog ID

        戻り値:
            bool: 削除成功時 True

        注意:
            この操作は永続的で取り消しできません
        """
        response = self._request("DELETE", f"/lifelogs/{lifelog_id}")
        return response.json().get("success", False)

    def search_lifelogs_by_date_range(
        self,
        start_date: str,
        end_date: str,
        search: Optional[str] = None,
        timezone: str = "Asia/Tokyo"
    ) -> List[Dict[str, Any]]:
        """
        日付範囲でLifelogsを検索（ページネーション自動処理）

        引数:
            start_date (str): 開始日 "YYYY-MM-DD"
            end_date (str): 終了日 "YYYY-MM-DD"
            search (str | None): 検索キーワード
            timezone (str): タイムゾーン（デフォルト: "Asia/Tokyo"）

        戻り値:
            list: 全Lifelogsのリスト
        """
        all_lifelogs = []
        cursor = None

        while True:
            result = self.list_lifelogs(
                start=f"{start_date}T00:00:00",
                end=f"{end_date}T23:59:59",
                search=search,
                timezone=timezone,
                cursor=cursor,
                limit=10
            )

            data = result.get("data", {})
            lifelogs = data.get("lifelogs", [])
            all_lifelogs.extend(lifelogs)

            # 次のページがあるか確認
            cursor = data.get("nextCursor")
            if not cursor:
                break

        return all_lifelogs

    # ---------------------------------------------------
    # Audio（音声）
    # ---------------------------------------------------

    def download_audio(
        self,
        start_ms: int,
        end_ms: int,
        save_path: str = "audio.ogg",
        audio_source: str = "pendant"
    ) -> str:
        """
        指定時間範囲の音声を Ogg Opus 形式でダウンロード

        引数:
            start_ms (int): 開始時刻（ミリ秒、Unix timestamp）
            end_ms (int): 終了時刻（ミリ秒、Unix timestamp）
            save_path (str): 保存先ファイルパス（デフォルト: "audio.ogg"）
            audio_source (str): 音声ソース（現在は "pendant" のみ対応）

        戻り値:
            str: 保存されたファイルパス

        注意:
            最大ダウンロード時間は2時間（7,200,000ms）

        使用例:
            # 1時間分の音声をダウンロード
            client.download_audio(
                start_ms=1705305600000,
                end_ms=1705309200000,
                save_path="meeting_20250115.ogg"
            )
        """
        # 時間範囲チェック（最大2時間）
        duration_ms = end_ms - start_ms
        max_duration_ms = 7_200_000  # 2時間

        if duration_ms > max_duration_ms:
            raise ValueError(
                f"ダウンロード時間が最大値（2時間）を超えています。\n"
                f"  要求時間: {duration_ms / 3600000:.2f}時間"
            )

        params = {
            "startMs": start_ms,
            "endMs": end_ms,
            "audioSource": audio_source
        }

        response = self._request("GET", "/download-audio", params=params)

        # ファイル保存
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

    def download_audio_from_lifelog(
        self,
        lifelog_id: str,
        save_path: Optional[str] = None
    ) -> str:
        """
        Lifelogから直接音声をダウンロード

        引数:
            lifelog_id (str): Lifelog ID
            save_path (str | None): 保存先パス（未指定時は自動生成）

        戻り値:
            str: 保存されたファイルパス
        """
        # Lifelogデータ取得
        lifelog = self.get_lifelog(lifelog_id)

        # タイムスタンプ抽出
        start_time = lifelog.get("data", {}).get("startTime")
        end_time = lifelog.get("data", {}).get("endTime")

        if not start_time or not end_time:
            raise ValueError(f"Lifelog {lifelog_id} に有効な時刻情報がありません。")

        # ISO 8601 → Unix timestamp (ms) 変換
        start_ms = int(datetime.fromisoformat(start_time.replace("Z", "+00:00")).timestamp() * 1000)
        end_ms = int(datetime.fromisoformat(end_time.replace("Z", "+00:00")).timestamp() * 1000)

        # 保存パス自動生成
        if not save_path:
            save_path = f"audio_{lifelog_id}.ogg"

        return self.download_audio(start_ms, end_ms, save_path)

    # ---------------------------------------------------
    # Chats（チャット）
    # ---------------------------------------------------

    def list_chats(
        self,
        limit: int = 50,
        direction: str = "desc",
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask AI チャットの一覧取得

        引数:
            limit (int): 取得件数（最大100、デフォルト50）
            direction (str): ソート順（"desc" または "asc"）
            cursor (str | None): ページネーション用カーソル

        戻り値:
            dict: チャット一覧とメタデータ
        """
        params = {
            "limit": min(limit, 100),  # 最大100に制限
            "direction": direction
        }

        if cursor:
            params["cursor"] = cursor

        response = self._request("GET", "/chats", params=params)
        return response.json()

    def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """
        特定のチャットを取得

        引数:
            chat_id (str): チャット ID

        戻り値:
            dict: チャットデータ
        """
        response = self._request("GET", f"/chats/{chat_id}")
        return response.json()

    def delete_chat(self, chat_id: str) -> bool:
        """
        チャットを削除

        引数:
            chat_id (str): 削除するチャット ID

        戻り値:
            bool: 削除成功時 True

        注意:
            ユーザーは自身のチャットのみ削除可能
        """
        response = self._request("DELETE", f"/chats/{chat_id}")
        return response.json().get("success", False)

    def get_all_chats(self, direction: str = "desc") -> List[Dict[str, Any]]:
        """
        すべてのチャットを取得（ページネーション自動処理）

        引数:
            direction (str): ソート順（"desc" または "asc"）

        戻り値:
            list: 全チャットのリスト
        """
        all_chats = []
        cursor = None

        while True:
            result = self.list_chats(limit=100, direction=direction, cursor=cursor)

            data = result.get("data", {})
            chats = data.get("chats", [])
            all_chats.extend(chats)

            # 次のページがあるか確認
            cursor = data.get("nextCursor")
            if not cursor:
                break

        return all_chats

    # ---------------------------------------------------
    # ユーティリティメソッド
    # ---------------------------------------------------

    def export_lifelogs_to_json(
        self,
        output_path: str,
        date: Optional[str] = None,
        search: Optional[str] = None
    ) -> str:
        """
        Lifelogsを JSON ファイルにエクスポート

        引数:
            output_path (str): 出力ファイルパス
            date (str | None): 日付フィルタ "YYYY-MM-DD"
            search (str | None): 検索クエリ

        戻り値:
            str: 出力ファイルパス
        """
        result = self.list_lifelogs(date=date, search=search, limit=10, include_contents=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return output_path

    def print_lifelog_summary(self, lifelog: Dict[str, Any]) -> None:
        """
        Lifelogの概要を見やすく表示

        引数:
            lifelog (dict): Lifelogデータ
        """
        print(f"ID: {lifelog.get('id')}")
        print(f"タイトル: {lifelog.get('title')}")
        print(f"開始時刻: {lifelog.get('startTime')}")
        print(f"終了時刻: {lifelog.get('endTime')}")
        print(f"スター: {'⭐️' if lifelog.get('isStarred') else '☆'}")

        # コンテンツがあれば表示
        if 'contents' in lifelog:
            print(f"コンテンツ: {lifelog['contents'][:100]}...")

        print("-" * 50)

    # ---------------------------------------------------
    # 文字起こし機能（Transcription）
    # ---------------------------------------------------

    def transcribe_audio_file(
        self,
        audio_file_path: str,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: Optional[str] = "ja",
        response_format: str = "json",
        timestamp_granularities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        OpenAI Whisper API を使って音声ファイルを文字起こし

        引数:
            audio_file_path (str): 音声ファイルのパス（.ogg, .mp3, .wav など）
            api_key (str | None): OpenAI APIキー。未指定時は環境変数 OPENAI_API_KEY から読み込む
            model (str): 使用するモデル（デフォルト: "whisper-1"）
            language (str | None): 音声の言語（例: "ja", "en"）
            response_format (str): レスポンス形式（"json", "text", "srt", "vtt", "verbose_json"）
            timestamp_granularities (list | None): タイムスタンプの粒度（["word", "segment"]）

        戻り値:
            dict: 文字起こし結果

        例外:
            ValueError: APIキーが設定されていない、またはファイルが存在しない場合
            RuntimeError: APIリクエストが失敗した場合

        使用例:
            result = client.transcribe_audio_file("audio.ogg")
            print(result["text"])
        """
        # OpenAI APIキーを取得
        openai_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError(
                "環境変数 OPENAI_API_KEY が設定されていません。\n"
                "OpenAI API キーを取得して設定してください:\n"
                "  export OPENAI_API_KEY=\"sk-...\""
            )

        # ファイル存在チェック
        if not os.path.exists(audio_file_path):
            raise ValueError(f"音声ファイルが見つかりません: {audio_file_path}")

        # OpenAI Whisper API エンドポイント
        url = "https://api.openai.com/v1/audio/transcriptions"

        # リクエストヘッダー
        headers = {
            "Authorization": f"Bearer {openai_key}"
        }

        # リクエストデータ
        data = {
            "model": model,
            "response_format": response_format
        }

        if language:
            data["language"] = language

        if timestamp_granularities:
            data["timestamp_granularities[]"] = timestamp_granularities

        # ファイルを開いてアップロード
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "file": audio_file
            }

            response = requests.post(url, headers=headers, data=data, files=files)

        # エラーチェック
        if response.status_code != 200:
            raise RuntimeError(
                f"Whisper API リクエストに失敗しました。\n"
                f"  Status: {response.status_code}\n"
                f"  Body: {response.text}"
            )

        # レスポンスを返す
        if response_format == "json" or response_format == "verbose_json":
            return response.json()
        else:
            return {"text": response.text}

    def transcribe_lifelog(
        self,
        lifelog_id: str,
        output_dir: Optional[str] = None,
        keep_audio: bool = False,
        api_key: Optional[str] = None,
        language: str = "ja"
    ) -> Dict[str, Any]:
        """
        Lifelogの音声をダウンロードして文字起こし（ワンストップ処理）

        引数:
            lifelog_id (str): Lifelog ID
            output_dir (str | None): 出力ディレクトリ（未指定時はカレントディレクトリ）
            keep_audio (bool): 音声ファイルを保持するか（デフォルト: False）
            api_key (str | None): OpenAI APIキー
            language (str): 音声の言語（デフォルト: "ja"）

        戻り値:
            dict: 文字起こし結果と関連情報

        使用例:
            result = client.transcribe_lifelog("lifelog_abc123")
            print(result["transcription"]["text"])
            print(f"保存先: {result['text_file']}")
        """
        # 出力ディレクトリを決定
        if output_dir is None:
            output_dir = "."

        # 音声をダウンロード
        audio_path = os.path.join(output_dir, f"audio_{lifelog_id}.ogg")
        print(f"🎵 音声をダウンロードしています: {lifelog_id}")
        self.download_audio_from_lifelog(lifelog_id, save_path=audio_path)
        print(f"✅ ダウンロード完了: {audio_path}")

        # 文字起こし実行
        print(f"🎤 文字起こしを実行しています...")
        transcription = self.transcribe_audio_file(
            audio_path,
            api_key=api_key,
            language=language,
            response_format="verbose_json"
        )
        print(f"✅ 文字起こし完了")

        # テキストファイルに保存
        text_file = os.path.join(output_dir, f"transcription_{lifelog_id}.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(transcription["text"])

        # JSON形式でも保存
        json_file = os.path.join(output_dir, f"transcription_{lifelog_id}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)

        # 音声ファイルを削除（keep_audio=False の場合）
        if not keep_audio and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"🗑️  音声ファイルを削除しました: {audio_path}")

        # 結果を返す
        return {
            "lifelog_id": lifelog_id,
            "transcription": transcription,
            "text_file": text_file,
            "json_file": json_file,
            "audio_file": audio_path if keep_audio else None
        }


# -----------------------------------------
# 動作テスト用 main
# -----------------------------------------

def main():
    """
    基本的な使用例
    """
    try:
        # クライアント初期化
        client = LimitlessClient()

        print("=" * 50)
        print("📋 最近のLifelogsを取得")
        print("=" * 50)

        lifelogs_result = client.list_lifelogs(limit=3)
        lifelogs = lifelogs_result.get("data", {}).get("lifelogs", [])

        if not lifelogs:
            print("Lifelogs が見つかりませんでした。")
        else:
            print(f"\n✅ {len(lifelogs)} 件の Lifelog を取得しました:\n")
            for log in lifelogs:
                client.print_lifelog_summary(log)

        print("\n" + "=" * 50)
        print("💬 最近のチャットを取得")
        print("=" * 50)

        chats_result = client.list_chats(limit=3)
        chats = chats_result.get("data", {}).get("chats", [])

        if not chats:
            print("チャットが見つかりませんでした。")
        else:
            print(f"\n✅ {len(chats)} 件のチャットを取得しました:\n")
            for chat in chats:
                print(f"ID: {chat.get('id')}")
                print(f"要約: {chat.get('summary', 'N/A')}")
                print(f"作成日時: {chat.get('createdAt')}")
                print("-" * 50)

        # 使用例: JSON エクスポート
        # today = datetime.now().strftime("%Y-%m-%d")
        # client.export_lifelogs_to_json(f"lifelogs_{today}.json", date=today)
        # print(f"\n✅ Lifelogs を lifelogs_{today}.json にエクスポートしました")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()

