from pydantic import BaseModel, Field
from typing import Optional, List


class ValidationErrorItem(BaseModel):
    loc: List[str] = Field(description="エラー箇所")
    message: str = Field(description="エラーメッセージ")
    type: str = Field(description="エラータイプ")


class Response(BaseModel):
    result: str = Field("success", description="実行結果 成功")


class FailureResponse(Response):
    result: str = Field("failure", description="実行結果 失敗")
    detail: str = Field(description="失敗 詳細メッセージ")


class ValidationErrorResponse(Response):
    result: str = Field("failure", description="エラー")
    detail: List[ValidationErrorItem] = Field(None, description="エラー")


class RedirectResponse(Response):
    result: str = Field("redirect", description="リダイレクト要求")
    status: int = Field(description="リダイレクトステータス")
    redirect_to: Optional[str] = Field(description="リダイレクト先URL")


class HelthCheckResponse(Response):
    license: str = Field(
        "Copyright 2026 Pignus. All rights reserved.", description="ライセンス")
