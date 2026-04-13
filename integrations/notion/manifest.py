
import os
from typing import Optional, List
from packman.integrations import notion


def database_propertys_by_id_or_url(id_or_url: str, api_key: Optional[str] = None) -> List[notion.raw.Property]:
    if api_key is None:
        api_key = os.getenv("NOTION_API_KEY")
    notion_client = notion.sdk_client.create_sdk_client(key=api_key)

    if notion_client:
        holder = notion.raw.RetrieveHolder(
            notion.sdk_client.get_database_retrieve_by_id(
                sdk_client=notion_client,
                database_id=notion.raw.make_database_id_from_url(id_or_url)
            )
        )
        if holder:
            return holder.find_all_properties()
