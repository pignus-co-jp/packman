# coding: utf-8

from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status
from fastapi import APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from fastapi import Header
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from . import dto

app = FastAPI()
_router = APIRouter()

_VERSION = "1.0"


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(dto.response.FailureResponse(detail=str(exc.detail))))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(exc.errors())
    ves = []
    for er in exc.errors():
        ls = []
        for tl in er["loc"]:
            ls.append(str(tl))
        ves.append(dto.response.ValidationErrorItem(
            loc=ls, message=str(er["msg"]), type=str(er["type"])))

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            dto.response.ValidationErrorResponse(detail=ves))
    )


def no_cors():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def get_router():
    return _router


def get_error_response():
    return {404: {"model": dto.response.FailureResponse}}


def get_crud_error_response():
    return {422: {"model": dto.response.ValidationErrorResponse}}


class PPapiResponse(dto.response.Response):
    version: str = Field(description="Pignusフレームワーク バージョン")
    license: str = Field(
        "Copyright 2026 Pignus. All rights reserved.", description="ライセンス")

    class Config:
        schema_extra = {
            "example": {
                "result": "success",
                "version": "1.0",
                "license": "Copyright 2026 Pignus. All rights reserved."
            }
        }


@_router.get("/ppapi", response_model=PPapiResponse, responses=get_error_response())
def health_check():
    ''' 疎通確認 '''
    return PPapiResponse(version=_VERSION)


@_router.get("/secure", response_model=PPapiResponse, dependencies=[Depends(HTTPBearer())], responses=get_error_response())
def sec_health_check():
    ''' 認証API疎通確認 '''
    return PPapiResponse(version=_VERSION)


def _entry():
    try:
        import ppapiboot
    except:
        pass


_entry()

app.include_router(router=_router)
