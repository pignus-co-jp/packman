# -*- coding: utf-8 -*-

"""
API DTO層 (API DTO Layer)
==================

このモジュールは、API層で使用するデータ転送オブジェクト（DTO）を定義します。
FastAPIとの連携を考慮し、Pydanticモデルを使用してリクエストとレスポンスのデータ構造を管理します。

# 構成要素

## request.py
- FastAPIリクエスト用のPydantic DTOクラス。入力データのバリデーションと型変換を担う。

## response.py
- FastAPIレスポンス用のPydantic DTOクラス。出力データの構造化とシリアライズを担う。
"""

from . import request
from . import response
