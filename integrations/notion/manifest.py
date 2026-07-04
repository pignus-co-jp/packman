
import os
from typing import Optional, List
from packman.integrations import notion


def database_propertys_by_id_or_url(id_or_url: str, api_key: Optional[str] = None) -> List[notion.raw.Property]:
    notion_client = notion.sdk_client.create_sdk_client(key=api_key)

    if notion_client:
        holder = notion.raw.RetrieveHolder(
            notion.sdk_client.get_database_retrieve_by_id(
                sdk_client=notion_client,
                database_id=notion.raw.make_database_id_from_url(id_or_url)
            )
        )
        if holder:
            return holder.list_all_properties()


def page_propertys_by_id_or_url(id_or_url: str, api_key: Optional[str] = None) -> List[notion.raw.Property]:
    notion_client = notion.sdk_client.create_sdk_client(key=api_key)

    if notion_client:
        holder = notion.raw.RetrieveHolder(
            notion.sdk_client.get_page_retrieve_by_id(
                sdk_client=notion_client,
                page_id=notion.raw.make_page_id_from_url(id_or_url)
            )
        )
        if holder:
            return holder.list_all_properties()
