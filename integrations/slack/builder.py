# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any


# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any


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
        self._elements.append({
            "type": "text",
            "text": content
        })
        return self

    def mentions(self, user_ids: List[str]) -> "MessageBuilder":
        mention_str = " ".join([f"<@{uid}>" for uid in user_ids])
        self._elements.append({
            "type": "text",
            "text": mention_str
        })
        return self

    # -------------------------
    # 装飾
    # -------------------------
    def bold(self, content: str) -> "MessageBuilder":
        self._elements.append({
            "type": "text",
            "text": content,
            "style": {"bold": True}
        })
        return self

    def italic(self, content: str) -> "MessageBuilder":
        self._elements.append({
            "type": "text",
            "text": content,
            "style": {"italic": True}
        })
        return self

    def strike(self, content: str) -> "MessageBuilder":
        self._elements.append({
            "type": "text",
            "text": content,
            "style": {"strike": True}
        })
        return self

    def code(self, content: str) -> "MessageBuilder":
        self._elements.append({
            "type": "text",
            "text": content,
            "style": {"code": True}
        })
        return self

    def codeblock(self, content: str) -> "MessageBuilder":
        self._elements.append({
            "type": "rich_text_preformatted",
            "elements": [
                {"type": "text", "text": content}
            ]
        })
        return self

    # -------------------------
    # Slack API 用 Payload 生成
    # -------------------------

    def to_blocks(self) -> Dict[str, Any]:
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
        parts: List[str] = []

        for el in self._elements:
            if el["type"] == "text":
                text = el["text"]
                style = el.get("style", {})

                if style.get("bold"):
                    text = f"*{text}*"
                if style.get("italic"):
                    text = f"_{text}_"
                if style.get("strike"):
                    text = f"~{text}~"
                if style.get("code"):
                    text = f"`{text}`"

                parts.append(text)

            elif el["type"] == "rich_text_preformatted":
                # コードブロック
                inner = "".join(e["text"] for e in el.get("elements", []))
                parts.append(f"```{inner}```")

        return " ".join(parts)
