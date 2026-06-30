from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.common.errors import AppError, ErrorCode
from app.config import settings
from app.routers import (
    assessments,
    audit,
    cases,
    clinical_assessment,
    explainability,
    images,
    longitudinal,
    notes,
    review,
    validation,
    vision,
)

app = FastAPI(title="Wound Care AI Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.media_root), name="media")

API_PREFIX = "/api/v1"
for router_module in (
    cases,
    assessments,
    images,
    vision,
    longitudinal,
    clinical_assessment,
    explainability,
    review,
    notes,
    validation,
    audit,
):
    app.include_router(router_module.router, prefix=API_PREFIX)


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": ErrorCode.VALIDATION_ERROR,
            "message": str(exc.errors()),
        },
    )


@app.get("/health")
def health() -> dict:
    return {"success": True, "data": {"status": "ok"}}
