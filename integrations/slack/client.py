# -*- coding: utf-8 -*-

from typing import List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from . import dto


class Slack:
    def __init__(self,
                 bot_token: str
                 ):
        self.bot_token = bot_token
        self.client = WebClient(token=bot_token)
        pass

    # -------------------------
    # ユーザー一覧取得
    # -------------------------
    def list_users(self) -> List[dto.User]:
        """
        - users:read はユーザー一覧取得に必須
        - users.list で email を取得するには users:read.email が必要
        """
        try:
            response = self.client.users_list()
        except SlackApiError:
            return []

        if not response.get("ok"):
            return []

        users: List[dto.User] = []
        for member in response["members"]:
            profile = member.get("profile", {})
            users.append(
                dto.User(
                    id=member["id"],
                    name=profile.get("display_name"),
                    display_name=profile.get("display_name"),
                    email=profile.get("email"),
                )
            )

        return users

    # -------------------------
    # メッセージ投稿（ts を返す）
    # -------------------------
    def post_message(
        self,
        text: str,
        channel: str,
    ) -> Optional[str]:
        """
        Slack にメッセージを投稿し、投稿されたメッセージの ts を返す。
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
            )
        except SlackApiError:
            print(f"Slack API Error: {e.response['error']}")
            return None

        if not response.get("ok"):
            return None

        return response.get("ts")

    def conversations(
            self,
            channel: str,
            limit: int = 100,
    ) -> List[dto.Conversation]:
        """
        指定チャンネルの最新メッセージを Conversation DTO のリストとして返す。
        """

        try:
            response = self.client.conversations_history(
                channel=channel,
                limit=limit
            )
        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            return []

        if not response.get("ok"):
            return []

        messages = response.get("messages", [])

        # DTO に変換
        conversations: List[dto.Conversation] = []
        for msg in messages:
            conversations.append(
                dto.Conversation(
                    ts=msg["ts"],
                    # bot_message など user が無い場合もある
                    user_id=msg.get("user", ""),
                    text=msg.get("text")
                )
            )

        return conversations

    def delete_by_ts(
        self,
        ts: str,
        channel: str,
    ) -> bool:

        try:
            response = self.client.chat_delete(channel=channel, ts=ts)
            if response.get("ok"):
                return True
        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            return False

        return False
