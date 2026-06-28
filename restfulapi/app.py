# coding: utf-8

from typing import List, Optional
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status, APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError

from . import dto


def _setup_cors_middleware(app: FastAPI):
    """ CORSミドルウェアの設定 (全許可) """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def _packman_error_handler(app: FastAPI):
    """ カスタムエラーハンドラーの登録 """
    # HTTP例外ハンドラー
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                dto.response.FailureResponse(detail=str(exc.detail)))
        )

    # バリデーション例外ハンドラー
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        ves = []
        for er in exc.errors():
            ls = [str(tl) for tl in er["loc"]]
            ves.append(
                dto.response.ValidationErrorItem(
                    loc=ls,
                    message=str(er["msg"]),
                    type=str(er["type"])
                )
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                dto.response.ValidationErrorResponse(detail=ves)
            )
        )


def _packman_router() -> APIRouter:
    """ ヘルスチェック用ルーターの生成 """
    router = APIRouter()

    @router.get("/health")
    def health():
        """ 疎通確認 """
        return dto.response.Response()

    return router


def create_web_app(prefix: str, routers: Optional[List[APIRouter]] = None) -> FastAPI:
    """ FastAPIアプリケーションのファクトリ関数 """
    app = FastAPI()
    
    # 共通設定の適用
    _setup_cors_middleware(app=app)
    _packman_error_handler(app=app)
    
    # 内部ルーターの登録
    app.include_router(_packman_router(), prefix="/packman")
    
    # 外部ルーターの登録
    if routers:
        for router in routers:
            app.include_router(router, prefix=prefix)
            
    return app