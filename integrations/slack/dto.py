# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional


class User(BaseModel):
    """
    Slack API (users.list / users.info) のユーザー情報を表す DTO。
    """
    id: str = Field(
        ...,
        description="Slack ユーザー ID（例: U123ABC）"
    )
    name: Optional[str] = Field(
        None,
        description="Slack の内部ユーザー名"
    )
    display_name: Optional[str] = Field(
        None,
        description="プロフィール上の表示名"
    )
    email: Optional[str] = Field(
        None,
        description="メールアドレス（users:read.email スコープが必要）"
    )


class Conversation(BaseModel):
    """
    Slack API (conversations.history / conversations.replies) の
    メッセージ情報を表す DTO。
    """
    ts: str = Field(
        ...,
        description="メッセージのタイムスタンプ（Slack 内での一意 ID）"
    )
    user_id: Optional[str] = Field(
        None,
        description="投稿者のユーザー ID（例: U123ABC）"
    )
    text: Optional[str] = Field(
        None,
        description="メッセージ本文（Bot / ユーザー / システム投稿を含む）"
    )

class Channel(BaseModel):
    """
    Slack API () のチャンネル情報を表す DTO。
    """
    id: str = Field(
        ...,
        description="Slack チャンネル ID（例: U123ABC）"
    )
    name: Optional[str] = Field(
        None,
        description="Slack のチャンネル名"
    )
