# -*- coding: utf-8 -*-

from typing import List, Dict, Any


class MessageBuilder:
    """
    Slack Rich Text 対応メッセージビルダー
    - text(), bold(), italic(), code() など従来 API を維持
    - 内部的には rich_text ブロックを構築
    - build() で Slack API に渡せる payload を生成
    """

    def __init__(self):
        self._elements: List[Dict[str, Any]] = []

    # -------------------------
    # 基本テキスト
    # -------------------------
    def text(self, content: str) -> "MessageBuilder":
        """プレーンテキストを追加"""
        if content:  # 空文字チェック
            self._elements.append({
                "type": "text",
                "text": content
            })
        return self

    def mentions(self, user_ids: List[str]) -> "MessageBuilder":
        """ユーザーメンションを追加"""
        if user_ids:  # 空リストチェック
            mention_str = " ".join([f"<@{uid}>" for uid in user_ids])
            self._elements.append({
                "type": "text",
                "text": mention_str
            })
        return self

    def newline(self) -> "MessageBuilder":
        """改行を追加"""
        self._elements.append({
            "type": "text",
            "text": "\n"
        })
        return self

    # -------------------------
    # 装飾
    # -------------------------
    def bold(self, content: str) -> "MessageBuilder":
        """太字テキストを追加"""
        if content:
            self._elements.append({
                "type": "text",
                "text": content,
                "style": {"bold": True}
            })
        return self

    def italic(self, content: str) -> "MessageBuilder":
        """斜体テキストを追加"""
        if content:
            self._elements.append({
                "type": "text",
                "text": content,
                "style": {"italic": True}
            })
        return self

    def strike(self, content: str) -> "MessageBuilder":
        """打ち消し線テキストを追加"""
        if content:
            self._elements.append({
                "type": "text",
                "text": content,
                "style": {"strike": True}
            })
        return self

    def code(self, content: str) -> "MessageBuilder":
        """インラインコードを追加"""
        if content:
            self._elements.append({
                "type": "text",
                "text": content,
                "style": {"code": True}
            })
        return self

    def codeblock(self, content: str, language: str = "") -> "MessageBuilder":
        """コードブロックを追加"""
        if content:
            element = {
                "type": "rich_text_preformatted",
                "elements": [
                    {"type": "text", "text": content}
                ]
            }
            # 言語指定があれば追加（Slackは一部対応）
            if language:
                element["border"] = 0  # Slack の実装による
            self._elements.append(element)
        return self

    def link(self, url: str, text: str = "") -> "MessageBuilder":
        """リンクを追加"""
        if url:
            self._elements.append({
                "type": "link",
                "url": url,
                "text": text or url
            })
        return self

    # -------------------------
    # 複合スタイル
    # -------------------------
    def styled_text(self, content: str, bold: bool = False, italic: bool = False,
                    strike: bool = False, code: bool = False) -> "MessageBuilder":
        """複数のスタイルを同時適用"""
        if content:
            style = {}
            if bold:
                style["bold"] = True
            if italic:
                style["italic"] = True
            if strike:
                style["strike"] = True
            if code:
                style["code"] = True

            element = {
                "type": "text",
                "text": content
            }
            if style:
                element["style"] = style

            self._elements.append(element)
        return self

    # -------------------------
    # ユーティリティ
    # -------------------------
    def clear(self) -> "MessageBuilder":
        """要素をクリア"""
        self._elements.clear()
        return self

    def is_empty(self) -> bool:
        """要素が空かチェック"""
        return len(self._elements) == 0

    # -------------------------
    # Slack API 用 Payload 生成
    # -------------------------
    def to_blocks(self) -> Dict[str, Any]:
        """Slack Blocks API形式で出力"""
        if not self._elements:
            return {"blocks": []}

        return {
            "blocks": [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": self._elements
                        }
                    ]
                }
            ]
        }

    # -------------------------
    # Markdown 風テキスト生成
    # -------------------------
    def to_string(self) -> str:
        """Markdown風の文字列として出力"""
        if not self._elements:
            return ""

        parts: List[str] = []

        for el in self._elements:
            el_type = el.get("type", "")

            if el_type == "text":
                text = el.get("text", "")
                style = el.get("style", {})

                # スタイル適用順序: code > bold > italic > strike
                if style.get("code"):
                    text = f"`{text}`"
                if style.get("bold"):
                    text = f"*{text}*"
                if style.get("italic"):
                    text = f"_{text}_"
                if style.get("strike"):
                    text = f"~{text}~"

                parts.append(text)

            elif el_type == "link":
                url = el.get("url", "")
                link_text = el.get("text", url)
                parts.append(f"[{link_text}]({url})")

            elif el_type == "rich_text_preformatted":
                # コードブロック
                inner = "".join(e.get("text", "")
                                for e in el.get("elements", []))
                parts.append(f"```\n{inner}\n```")

        return "".join(parts)  # スペース区切りではなく連結

    def __str__(self) -> str:
        """文字列表現"""
        return self.to_string()

    def __repr__(self) -> str:
        """デバッグ用表現"""
        return f"MessageBuilder(elements={len(self._elements)})"
