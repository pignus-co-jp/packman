

from typing import List, Optional
from . import raw

import notion_client



def create_sdk_client(key: str) -> Optional[notion_client.Client]:
    try:
        return notion_client.Client(auth=key)
    except Exception:
        return None


def make_database_id_from_url(url: str) -> Optional[str]:
    return None


def make_page_id_from_url(url: str) -> Optional[str]:
    return None


def create_search_filter():
    return None


def find_page_ids_by_database_id(sdk_client: notion_client.Client,
                                 database_id: str,
                                 search_filter: Optional[dict] = None) -> List[str]:
    """
    データベース内の全ページのIDをリストで取得する
    """
    page_ids = []
    try:
        cursor = None

        while True:
            # データベースをクエリ（1回につき最大100件）
            # 共通の引数を準備
            query_args = {
                "database_id": database_id,
                "start_cursor": cursor
            }

            # filter_objが指定されている場合のみ、引数に追加する
            if search_filter is not None:
                query_args["filter"] = search_filter

            # 辞書を展開して渡す
            response = sdk_client.databases.query(**query_args)

            # 結果からページIDを抽出
            for page in response.get("results", []):
                page_ids.append(page.get("id"))

            # 次のページがあるか確認
            if not response.get("has_more"):
                break

            cursor = response.get("next_cursor")
    except Exception as ex:
        print(ex)

    return page_ids


def get_page_property_by_page_id(sdk_client: notion_client.Client,
                                 page_id: str) -> Optional[dict]:
    try:
        return sdk_client.pages.retrieve(page_id=page_id)
    except Exception:
        return None


def get_body_only_markdown_by_block_id(sdk_client: notion_client.Client,
                                       block_id: str,
                                       indent: int = 0):
    """
    指定したIDのブロック配下（本文）を再帰的にMarkdown化
    """
    lines = []
    cursor = None
    prefix = "  " * indent  # 階層に応じたインデント

    while True:
        response = sdk_client.blocks.children.list(
            block_id=block_id, start_cursor=cursor)
        for block in response.get("results", []):
            md = raw.block_to_markdown(block)

            if md:
                lines.append(f"{prefix}{md}")

            # 子ブロック（ネストされたリストやトグル）の処理
            if block.get("has_children"):
                child_md = get_body_only_markdown_by_block_id(
                    sdk_client, block["id"], indent + 1)
                lines.append(child_md)
                if block.get("type") == "toggle":
                    lines.append(f"{prefix}</details>")

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return "\n".join(lines)


def get_body_only_markdown_by_page_id(sdk_client: notion_client.Client,
                                      page_id: str) -> str:
    """
    ページIDを親ブロックとして、その配下の本文をMarkdown化して取得
    """
    return get_body_only_markdown_by_block_id(sdk_client=sdk_client, 
                                              block_id=page_id)
