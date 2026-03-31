
from pydantic import BaseModel, Field
from typing import Optional, List


class Response(BaseModel):
    result: str = Field("success", description="実行結果 成功")

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "result": "success"
    #         }
    #     }


class ValidationErrorItem(BaseModel):
    loc: List[str] = Field(description="エラー箇所")
    message: str = Field(description="エラーメッセージ")
    type: str = Field(description="エラータイプ")

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "loc": ["query", "limit"],
    #             "message": "value is not a valid integer",
    #             "type": "type_error.integer"
    #         }
    #     }


class FailureResponse(Response):
    result: str = Field("failure", description="実行結果 失敗")
    detail: str = Field(description="失敗 詳細メッセージ")

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "result": "failure",
    #             "detail": "Not Found"
    #         }
    #     }


class ValidationErrorResponse(Response):
    result: str = Field("failure", description="エラー")
    detail: List[ValidationErrorItem] = Field(None, description="エラー")

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "result": "failure",
    #             "detail": [
    #                 {
    #                     "loc": ["query", "limit"],
    #                     "message": "value is not a valid integer",
    #                     "type": "type_error.integer"
    #                 }
    #             ]
    #         }
    #     }
