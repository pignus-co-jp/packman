# coding: utf-8

from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status, APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError

from . import dto


def create() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(dto.response.FailureResponse(detail=str(exc.detail))))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
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

    router = APIRouter()

    # response_model に指定し、関数からそのインスタンスを返します
    @router.get("/health_check")
    def health_check():  # 3. ルーティング関数にアンダースコア(_)は基本的に付けない
        """ 疎通確認 """
        return {
            "result": "success"
        }

    app.include_router(router, prefix="/packman")
    return app
