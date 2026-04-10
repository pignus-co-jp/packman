import os
import time
from typing import List, Optional

import requests

from ... import log

from ...config import env


def find_ad_ids_by_account_id(token: str,
                              account_id: str,
                              limit: int = 10,
                              extr_fields_query_param: Optional[str] = None
                              ):
    """
    指定したアカウントIDの広告一覧(idやname)を取得する。

    本関数は1ページ分のレスポンスのみを返す。
    全件取得が必要な場合は、呼び出し元でページネーションを処理すること。

    Example:
        url = None
        while True:
            res = find_ad_ids_by_account_id(token, account_id)
            process(res["data"])

            url = res.get("paging", {}).get("next")
            if not url:
                break

    Args:
        token (str): アクセストークン
        account_id (str): Facebookアカウント ID（act_ プレフィックスなし）
        limit (int): 1ページあたりの取得件数（デフォルト: 10）

    Returns:
        dict: Graph APIのレスポンス。`data` リストと `paging` を含む。
              エラー時は None を返す。
    """

    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    _extr_fields_query_param = ""
    if extr_fields_query_param:
        _extr_fields_query_param = "f,{extr_fields_query_param}"
    try:
        log.i("get_image_by_name",
              f"https://graph.facebook.com/v23.0/act_{account_id}/ads?fields=id,name,created_time{_extr_fields_query_param}&limit={limit}")
        x = requests.get(
            f"https://graph.facebook.com/v23.0/act_{account_id}/ads?fields=id,name,created_time{_extr_fields_query_param}&limit={limit}",
            headers=headers,
            timeout=60*2)
        return x.json()
    except Exception as ex:
        log.e("find_ad_ids_by_account_id", ex)
        pass

    return None


def get_ad_by_ad_id(token: str,
                    ad_id: str,
                    extr_fields_query_param: Optional[str] = None
                    ):

    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    _extr_fields_query_param = ""
    if extr_fields_query_param:
        _extr_fields_query_param = "f,{extr_fields_query_param}"

    try:
        url = (
            f"https://graph.facebook.com/v23.0/{ad_id}"
            "?fields=id,name,adset_id,campaign_id,status,"
            "created_time,updated_time,"
            "creative{id,name,object_story_spec,asset_feed_spec}"
            f"{_extr_fields_query_param}"
        )

        log.i("get_ad_by_ad_id", url)
        x = requests.get(url,
                         headers=headers,
                         timeout=60*2)
        return x.json()
    except Exception as ex:
        log.e("get_ad_by_ad_id", ex)
        pass

    return None


def get_image_by_name(token: str,
                      account_id: str,
                      image_name: str,
                      ):
    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    try:
        log.i("get_image_by_name",
              f"https://graph.facebook.com/v23.0/act_{account_id}/adimages?name={image_name}")
        x = requests.get(
            f"https://graph.facebook.com/v23.0/act_{account_id}/adimages?name={image_name}",
            headers=headers,
            timeout=60*2)
        return x.json()
    except Exception as ex:
        log.e("get_image_by_name", ex)
        pass

    return None


def upload_image(token: str,
                 account_id: str,
                 image_path: str,
                 ):
    if not token:
        raise ValueError("token is required")

    if os.path.exists(image_path):
        headers = {}
        headers["Authorization"] = f"Bearer {token}"
        # headers["Content-Type"] = "application/json"

        try:
            log.i("upload_image",
                  f'https://graph.facebook.com/v23.0/act_{account_id}/adimages',
                  image_path)
            with open(image_path, 'rb') as f:
                files = {'filename': f}
                x = requests.post(
                    f'https://graph.facebook.com/v23.0/act_{account_id}/adimages',
                    files=files,
                    headers=headers,
                    timeout=60*2)
                return x.json()
        except Exception as ex:
            log.e("upload_image", ex)
            pass

    return None


def get_video_by_name(token: str,
                      account_id: str,
                      video_name: str,
                      ):
    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    try:
        log.i("get_video_by_name",
              f"https://graph.facebook.com/v23.0/act_{account_id}/advideos?name={video_name}")
        x = requests.get(
            f"https://graph.facebook.com/v23.0/act_{account_id}/advideos?name={video_name}",
            headers=headers,
            timeout=60*2)
        return x.json()
    except Exception as ex:
        log.e("get_video_by_name", ex)
        pass
    return None


def get_video_thumbnails_by_video_id(token: str,
                                     video_id: str,
                                     ):
    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    try:
        log.i("get_video_thumbnails_by_video_id",
              f"https://graph.facebook.com/v23.0/{video_id}/thumbnails"
              )
        x = requests.get(
            f"https://graph.facebook.com/v23.0/{video_id}/thumbnails",
            headers=headers,
            timeout=60*2)
        return x.json()
    except Exception as ex:
        log.e("get_video_thumbnails_by_video_id", ex)
        pass
    return None


def get_video_thumbnails_with_retry(token: str,
                                    video_id: str,
                                    max_retries: Optional[int] = 5,
                                    delay: Optional[int] = 6
                                    ):
    if not token:
        raise ValueError("token is required")

    """サムネイルが生成されるまでリトライ"""
    for attempt in range(max_retries):
        thumbnails = get_video_thumbnails_by_video_id(token=token,
                                                      video_id=video_id)

        if thumbnails and thumbnails.get('data') and len(thumbnails['data']) > 0:
            return thumbnails

        if attempt < max_retries - 1:
            print(f"サムネイル未生成、{delay}秒後にリトライ ({attempt + 1}/{max_retries})")
            time.sleep(delay)

    print("サムネイル取得タイムアウト")
    return None


def upload_video(token: str,
                 account_id: str,
                 video_path: str,
                 video_name: Optional[str] = None,
                 ):
    if not token:
        raise ValueError("token is required")

    if os.path.exists(video_path):
        headers = {}
        headers["Authorization"] = f"Bearer {token}"
        # headers["Content-Type"] = "application/json"

        video_title = os.path.basename(video_path)
        if video_name:
            video_title = video_name

        data = {
            'title': video_title,
        }

        try:
            log.i("upload_video",
                  f'https://graph.facebook.com/v23.0/act_{account_id}/advideos',
                  video_path)
            with open(video_path, 'rb') as f:
                files = {'source': f}
                x = requests.post(
                    f'https://graph.facebook.com/v23.0/act_{account_id}/advideos',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60*2)
                return x.json()
        except Exception as ex:
            log.e("upload_video", ex)
            pass

    return None


def _safe_request(adsjson: any):
    if adsjson:
        if "status" in adsjson:
            if adsjson["status"] == "PAUSED":
                return adsjson
    return None


def _validateonly_request(adsjson: any):
    if adsjson:
        safejsn = _safe_request(adsjson=adsjson)
        if safejsn:
            safejsn["execution_options"] = [
                "validate_only", "include_recommendations"]
            for x in safejsn["execution_options"]:
                if x == "validate_only":
                    return safejsn
    return None


def validateonly_ads(token: str,
                     account_id: str,
                     adsjson: any):
    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    request_adsjson = _validateonly_request(adsjson)

    if request_adsjson:
        try:
            log.i("validateonly_ads",
                  f"https://graph.facebook.com/v23.0/act_{account_id}/ads")
            x = requests.post(f"https://graph.facebook.com/v23.0/act_{account_id}/ads",
                              headers=headers,
                              json=request_adsjson,
                              timeout=60*2)
            return x.json()
        except Exception as ex:
            log.e("validateonly_ads", ex)


def regist_ads(token: str,
               account_id: str,
               adsjson: any):
    if not token:
        raise ValueError("token is required")

    headers = {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    if ((env.get_env_by_key("REGISTMODE_A") is None) or
            (str(env.get_env_by_key("REGISTMODE_A")) !=
             str(env.get_env_by_key("REGISTMODE_B")))
        ):
        log.i("regist_ads", "NoRegistMode", account_id, adsjson)
        return False

    request_adsjson = _safe_request(adsjson)

    if request_adsjson:
        try:
            log.i("regist_ads",
                  f"https://graph.facebook.com/v23.0/act_{account_id}/ads")
            x = requests.post(f"https://graph.facebook.com/v23.0/act_{account_id}/ads",
                              headers=headers,
                              json=request_adsjson,
                              timeout=60*2)
            return x.json()
        except Exception as ex:
            log.e("regist_ads", ex)
