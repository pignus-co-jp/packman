

from typing import List, Optional, Dict


class DbProperty:
    def __init__(self,
                 name: str,
                 raw: dict):
        self._name = name
        self._raw = raw or {}

    def get_id(self) -> Optional[str]:
        return self._raw.get("id")

    def get_name(self) -> str:
        return self._name

    def get_type(self) -> Optional[str]:
        """'select', 'multi_select', 'date' などの型名を返す"""
        return self._raw.get("type")

    def get_value_dict(self) -> dict:
        """
        'type' に紐づく詳細データ（selectの内容など）を返す
        例: typeが 'select' なら self._raw['select'] を返す
        """
        p_type = self.get_type()
        if p_type and p_type in self._raw:
            return self._raw[p_type]
        return {}

    def get_raw(self) -> dict:
        return self._raw

    def find_plain_text_contents(self) -> List[str]:
        # 内部関数を外に出すか、selfを渡さずに済むよう raw全体を渡す
        return self._parse_property_recursive(self._raw)

    def _parse_property_recursive(self, prop_data: dict) -> List[str]:
        if not prop_data or not isinstance(prop_data, dict):
            return []

        p_type = prop_data.get("type")
        if not p_type:
            return []

        raw_val = prop_data.get(p_type)
        if raw_val is None:
            return []

        plain_texts: List[str] = []

        # 1. テキスト系
        if p_type in ["title", "rich_text"]:
            text = "".join(t.get("plain_text", "")
                           for t in raw_val if isinstance(t, dict))
            plain_texts = [text]

        # 2. 選択・ステータス系
        elif p_type in ["select", "status"]:
            plain_texts = [raw_val.get("name", "")] if raw_val else []

        elif p_type == "multi_select":
            plain_texts = [m.get("name", "") for m in raw_val]

        # 3. 日付系 (start, endを個別の要素として格納)
        elif p_type == "date":
            if raw_val:
                start = raw_val.get("start")
                end = raw_val.get("end")
                if start:
                    plain_texts.append(start)
                else:
                    plain_texts.append("")
                if end:
                    plain_texts.append(end)
                else:
                    plain_texts.append("")

        # 4. ユーザー系 (作成者、編集者、ユーザー)
        elif p_type in ["people", "created_by", "last_edited_by"]:
            if isinstance(raw_val, list):
                plain_texts = [
                    u.get("name") or u.get("id") for u in raw_val]
            elif raw_val:
                plain_texts = [raw_val.get("name") or raw_val.get("id")]

        # 5. ファイル系 (URLのリスト)
        elif p_type == "files":
            for f in raw_val:
                f_type = f.get("type")
                url = f.get(f_type, {}).get("url", "")
                if url:
                    plain_texts.append(url)

        # 6. リレーション系 (関連ページIDのリスト)
        elif p_type == "relation":
            plain_texts = [r.get("id") for r in raw_val]

        # 7. ロールアップ系 (ここが重要)
        elif p_type == "rollup":
            r_type = raw_val.get("type")
            if r_type == "array":
                for item in raw_val.get("array", []):
                    # 各要素を再帰的に処理
                    plain_texts.extend(self._parse_property_recursive(item))
            else:
                # number, date などの単一値
                val = raw_val.get(r_type)
                if val is not None:
                    plain_texts = [str(val)]

        # (中略: formula, unique_id 等)

        return [t for t in plain_texts if t]  # 空文字を除去して返す


class DbHeader:
    def __init__(self,
                 raw: dict):
        # 探索を高速化するために辞書で保持する
        self._properties_by_name: Dict[str, DbProperty] = {}
        self._properties_by_id: Dict[str, DbProperty] = {}

        if not raw:
            return

        for k, v in raw.items():
            prop = DbProperty(k, v)
            self._properties_by_name[k] = prop

            p_id = prop.get_id()
            if p_id:
                self._properties_by_id[p_id] = prop

    def get_property_by_name(self, name: str) -> Optional[DbProperty]:
        return self._properties_by_name.get(name)

    def get_property_by_id(self, id: str) -> Optional[DbProperty]:
        return self._properties_by_id.get(id)

    def get_all_properties(self) -> List[DbProperty]:
        return list(self._properties_by_name.values())


class DbRetrieve:
    def __init__(self,
                 raw: dict):
        # raw.get("properties") が None の場合に備え {} をデフォルトに
        properties_raw = raw.get("properties", {}) if raw else {}
        self._header = DbHeader(properties_raw)

    def get_property_by_name(self, name: str) -> Optional[DbProperty]:
        return self._header.get_property_by_name(name)

    def get_property_by_id(self, id: str) -> Optional[DbProperty]:
        return self._header.get_property_by_id(id)

    def find_all_properties(self) -> List[DbProperty]:
        return self._header.get_all_properties()


def block_to_markdown(block: dict) -> str:
    """
    Notionの各ブロックをMarkdown記法に変換
    """
    b_type = block.get("type")
    content = block.get(b_type, {})
    md_text = ""

    # テキスト抽出
    rich_text = content.get("rich_text", [])
    text = "".join([t.get("plain_text", "") for t in rich_text])

    # ブロックタイプ別の変換ロジック
    if b_type == "paragraph":
        md_text = text
    elif b_type == "heading_1":
        md_text = f"# {text}"
    elif b_type == "heading_2":
        md_text = f"## {text}"
    elif b_type == "heading_3":
        md_text = f"### {text}"
    elif b_type == "bulleted_list_item":
        md_text = f"- {text}"
    elif b_type == "numbered_list_item":
        md_text = f"1. {text}"
    elif b_type == "to_do":
        checked = "x" if content.get("checked") else " "
        md_text = f"- [{checked}] {text}"
    elif b_type == "toggle":
        md_text = f"<details><summary>{text}</summary>"
    elif b_type == "code":
        lang = content.get("language", "text")
        md_text = f"```{lang}\n{text}\n```"
    elif b_type == "quote":
        md_text = f"> {text}"
    elif b_type == "divider":
        md_text = "---"
    elif b_type in ["image", "video", "file", "pdf"]:
        f_type = content.get("type")
        url = content.get(f_type, {}).get("url", "")
        # 画像ならMarkdown記法、それ以外はリンク記法
        md_text = f"![image]({url})" if b_type == "image" else f"[{b_type.upper()}]({url})"
    elif b_type == "callout":
        emoji = content.get("icon", {}).get("emoji", "💡")
        md_text = f"> {emoji} {text}"

    return md_text

