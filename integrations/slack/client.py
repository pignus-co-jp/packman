# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any


from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from . import dto

from ... import log


class SlackError(Exception):
    """Slack操作関連のエラー基底クラス"""
    pass


class SlackAPIError(SlackError):
    """Slack API呼び出しエラー"""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class Slack:
    """
    Slack API クライアントのラッパークラス

    必要な権限スコープ:
    - users:read: ユーザー一覧取得
    - users:read.email: メールアドレス取得
    - chat:write: メッセージ投稿
    - channels:history: チャンネル履歴取得
    - groups:history: プライベートチャンネル履歴取得
    - im:history: ダイレクトメッセージ履歴取得
    """

    def __init__(
        self,
        bot_token: str,
        timeout: int = 30,
        retry_handlers: Optional[List] = None,
    ):
        """
        Args:
            bot_token: Slack Bot Token
            timeout: APIリクエストのタイムアウト秒数
            retry_handlers: リトライハンドラーのリスト
        """
        self.client = WebClient(
            token=bot_token,
            timeout=timeout,
            retry_handlers=retry_handlers,
        )

    def _handle_api_error(self, e: SlackApiError, operation: str) -> None:
        """
        Slack APIエラーを統一的に処理

        Args:
            e: SlackApiError例外
            operation: 実行していた操作名
        """
        error_msg = e.response.get("error", "Unknown error")
        log.e(f"{operation} failed: {error_msg}")
        raise SlackAPIError(
            f"{operation} failed: {error_msg}",
            error_code=error_msg
        )

    # -------------------------
    # ユーザー一覧取得
    # -------------------------
    def list_users(
        self,
        include_bots: bool = False,
        cursor: Optional[str] = None,
        limit: int = 200,
    ) -> List[dto.User]:
        """
        Slackワークスペースのユーザー一覧を取得

        Args:
            include_bots: Botユーザーを含めるか
            cursor: ページネーション用カーソル
            limit: 1回の取得で返す最大件数（デフォルト200）

        Returns:
            ユーザーのリスト

        必要な権限:
            - users:read: ユーザー一覧取得
            - users:read.email: メールアドレス取得
        """
        try:
            response = self.client.users_list(
                cursor=cursor,
                limit=limit,
            )
        except SlackApiError as e:
            self._handle_api_error(e, "users_list")
            return []

        if not response.get("ok"):
            log.w("users_list returned ok=False")
            return []

        users: List[dto.User] = []
        for member in response.get("members", []):
            # Botを除外するオプション
            if not include_bots and member.get("is_bot", False):
                continue

            # 削除済みユーザーをスキップ
            if member.get("deleted", False):
                continue

            profile = member.get("profile", {})
            users.append(
                dto.User(
                    id=member["id"],
                    name=member.get("name"),  # ユーザー名も取得
                    display_name=profile.get(
                        "display_name") or profile.get("real_name"),
                    email=profile.get("email"),
                )
            )

        return users

    def list_all_users(self, include_bots: bool = False) -> List[dto.User]:
        """
        全ユーザーを取得（ページネーション対応）

        Args:
            include_bots: Botユーザーを含めるか

        Returns:
            全ユーザーのリスト
        """
        all_users: List[dto.User] = []
        cursor = None

        while True:
            try:
                response = self.client.users_list(
                    cursor=cursor,
                    limit=200,
                )
            except SlackApiError as e:
                self._handle_api_error(e, "users_list (pagination)")
                break

            if not response.get("ok"):
                break

            for member in response.get("members", []):
                if not include_bots and member.get("is_bot", False):
                    continue
                if member.get("deleted", False):
                    continue

                profile = member.get("profile", {})
                all_users.append(
                    dto.User(
                        id=member["id"],
                        name=member.get("name"),
                        display_name=profile.get(
                            "display_name") or profile.get("real_name"),
                        email=profile.get("email"),
                    )
                )

            # 次のページがあるかチェック
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return all_users

    # -------------------------
    # メッセージ投稿
    # -------------------------
    def post_message(
        self,
        text: str,
        channel: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        unfurl_links: bool = True,
        unfurl_media: bool = True,
    ) -> Optional[str]:
        """
        Slack にメッセージを投稿し、投稿されたメッセージの ts を返す

        Args:
            text: メッセージテキスト（blocksがある場合はフォールバック用）
            channel: チャンネルID or チャンネル名
            thread_ts: スレッドの親メッセージのts（スレッド返信の場合）
            blocks: Block Kit形式のブロック
            attachments: メッセージ添付
            unfurl_links: リンクを展開するか
            unfurl_media: メディアを展開するか

        Returns:
            投稿されたメッセージのts、失敗時はNone

        必要な権限:
            - chat:write: メッセージ投稿
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text,
                "unfurl_links": unfurl_links,
                "unfurl_media": unfurl_media,
            }

            if thread_ts:
                kwargs["thread_ts"] = thread_ts

            if blocks:
                kwargs["blocks"] = blocks

            if attachments:
                kwargs["attachments"] = attachments

            response = self.client.chat_postMessage(**kwargs)

        except SlackApiError as e:
            self._handle_api_error(e, "chat_postMessage")
            return None

        if not response.get("ok"):
            log.w("chat_postMessage returned ok=False")
            return None

        return response.get("ts")

    def post_ephemeral(
        self,
        text: str,
        channel: str,
        user: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        一時的なメッセージを投稿（特定のユーザーにのみ表示）

        Args:
            text: メッセージテキスト
            channel: チャンネルID
            user: 表示対象のユーザーID
            blocks: Block Kit形式のブロック

        Returns:
            投稿されたメッセージのts、失敗時はNone
        """
        try:
            kwargs = {
                "channel": channel,
                "user": user,
                "text": text,
            }

            if blocks:
                kwargs["blocks"] = blocks

            response = self.client.chat_postEphemeral(**kwargs)

        except SlackApiError as e:
            self._handle_api_error(e, "chat_postEphemeral")
            return None

        if not response.get("ok"):
            return None

        return response.get("message_ts")

    # -------------------------
    # メッセージ更新
    # -------------------------
    def update_message(
        self,
        ts: str,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        既存のメッセージを更新

        Args:
            ts: 更新するメッセージのts
            channel: チャンネルID
            text: 新しいテキスト
            blocks: 新しいブロック

        Returns:
            成功時True
        """
        try:
            kwargs = {
                "channel": channel,
                "ts": ts,
            }

            if text is not None:
                kwargs["text"] = text

            if blocks is not None:
                kwargs["blocks"] = blocks

            response = self.client.chat_update(**kwargs)
            return response.get("ok", False)

        except SlackApiError as e:
            self._handle_api_error(e, "chat_update")
            return False

    # -------------------------
    # 会話履歴取得
    # -------------------------
    def get_conversations(
        self,
        channel: str,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        inclusive: bool = False,
        cursor: Optional[str] = None,
    ) -> List[dto.Conversation]:
        """
        指定チャンネルのメッセージを Conversation DTO のリストとして返す

        Args:
            channel: チャンネルID
            limit: 取得する最大件数（1-1000、デフォルト100）
            oldest: この時刻以降のメッセージを取得（Unixタイムスタンプ）
            latest: この時刻以前のメッセージを取得（Unixタイムスタンプ）
            inclusive: oldest/latestを含むか
            cursor: ページネーション用カーソル

        Returns:
            会話のリスト

        必要な権限:
            - channels:history: パブリックチャンネル
            - groups:history: プライベートチャンネル
            - im:history: ダイレクトメッセージ
        """
        try:
            kwargs = {
                "channel": channel,
                "limit": min(limit, 1000),  # API制限
            }

            if oldest:
                kwargs["oldest"] = oldest
            if latest:
                kwargs["latest"] = latest
            if inclusive:
                kwargs["inclusive"] = inclusive
            if cursor:
                kwargs["cursor"] = cursor

            response = self.client.conversations_history(**kwargs)

        except SlackApiError as e:
            self._handle_api_error(e, "conversations_history")
            return []

        if not response.get("ok"):
            log.w("conversations_history returned ok=False")
            return []

        messages = response.get("messages", [])

        # DTO に変換
        conversations: List[dto.Conversation] = []
        for msg in messages:
            conversations.append(
                dto.Conversation(
                    ts=msg.get("ts", ""),
                    user_id=msg.get("user", ""),  # bot_messageなどはuserなし
                    text=msg.get("text", ""),
                )
            )

        return conversations

    def get_thread_replies(
        self,
        channel: str,
        thread_ts: str,
        limit: int = 100,
    ) -> List[dto.Conversation]:
        """
        スレッドの返信を取得

        Args:
            channel: チャンネルID
            thread_ts: スレッドの親メッセージのts
            limit: 取得する最大件数

        Returns:
            スレッド内の会話リスト
        """
        try:
            response = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=min(limit, 1000),
            )
        except SlackApiError as e:
            self._handle_api_error(e, "conversations_replies")
            return []

        if not response.get("ok"):
            return []

        messages = response.get("messages", [])

        conversations: List[dto.Conversation] = []
        for msg in messages:
            conversations.append(
                dto.Conversation(
                    ts=msg.get("ts", ""),
                    user_id=msg.get("user", ""),
                    text=msg.get("text", ""),
                )
            )

        return conversations

    # -------------------------
    # メッセージ削除
    # -------------------------
    def delete_message(
        self,
        ts: str,
        channel: str,
    ) -> bool:
        """
        メッセージを削除

        Args:
            ts: 削除するメッセージのts
            channel: チャンネルID

        Returns:
            成功時True

        必要な権限:
            - chat:write: メッセージ削除（自分が投稿したメッセージ）
        """
        try:
            response = self.client.chat_delete(
                channel=channel,
                ts=ts,
            )
            return response.get("ok", False)

        except SlackApiError as e:
            self._handle_api_error(e, "chat_delete")
            return False

    # -------------------------
    # リアクション関連
    # -------------------------
    def add_reaction(
        self,
        name: str,
        channel: str,
        timestamp: str,
    ) -> bool:
        """
        メッセージにリアクションを追加

        Args:
            name: 絵文字名（":"なし、例: "thumbsup"）
            channel: チャンネルID
            timestamp: メッセージのts

        Returns:
            成功時True
        """
        try:
            response = self.client.reactions_add(
                name=name,
                channel=channel,
                timestamp=timestamp,
            )
            return response.get("ok", False)

        except SlackApiError as e:
            # already_reacted エラーは無視
            if e.response.get("error") == "already_reacted":
                return True
            self._handle_api_error(e, "reactions_add")
            return False

    def remove_reaction(
        self,
        name: str,
        channel: str,
        timestamp: str,
    ) -> bool:
        """
        メッセージからリアクションを削除

        Args:
            name: 絵文字名（":"なし）
            channel: チャンネルID
            timestamp: メッセージのts

        Returns:
            成功時True
        """
        try:
            response = self.client.reactions_remove(
                name=name,
                channel=channel,
                timestamp=timestamp,
            )
            return response.get("ok", False)

        except SlackApiError as e:
            self._handle_api_error(e, "reactions_remove")
            return False

    # -------------------------
    # チャンネル関連
    # -------------------------
    def list_channels(
        self,
        exclude_archived: bool = True,
        types: str = "public_channel",
    ) -> List[dto.Channel]:
        """
        チャンネル一覧を取得

        Args:
            exclude_archived: アーカイブ済みを除外
            types: チャンネルタイプ（public_channel, private_channel, mpim, im）

        Returns:
            チャンネル情報のリスト
        """
        try:
            response = self.client.conversations_list(
                exclude_archived=exclude_archived,
                types=types,
            )
        except SlackApiError as e:
            self._handle_api_error(e, "conversations_list")
            return []

        if not response.get("ok"):
            return []

        channels: List[dto.Channel] = []
        xs = response.get("channels", [])
        for x in xs:
            channels.append(
                dto.Channel(
                    id=x.get("id", ""),
                    name=x.get("name", None)
                )
            )

        return channels

    def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """
        チャンネル情報を取得

        Args:
            channel: チャンネルID

        Returns:
            チャンネル情報、失敗時はNone
        """
        try:
            response = self.client.conversations_info(channel=channel)
        except SlackApiError as e:
            self._handle_api_error(e, "conversations_info")
            return None

        if not response.get("ok"):
            return None

        return response.get("channel")

    # -------------------------
    # ユーティリティ
    # -------------------------
    def get_user_info(self, user_id: str) -> Optional[dto.User]:
        """
        特定ユーザーの情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            ユーザー情報、失敗時はNone
        """
        try:
            response = self.client.users_info(user=user_id)
        except SlackApiError as e:
            self._handle_api_error(e, "users_info")
            return None

        if not response.get("ok"):
            return None

        member = response.get("user", {})
        profile = member.get("profile", {})

        return dto.User(
            id=member["id"],
            name=member.get("name"),
            display_name=profile.get(
                "display_name") or profile.get("real_name"),
            email=profile.get("email"),
        )
