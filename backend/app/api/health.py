from fastapi import APIRouter, Request

from app.dependencies import response_envelope, serialize_database_target


router = APIRouter()


@router.get("/health")
def health(request: Request):
    settings = request.app.state.settings
    return response_envelope(
        request,
        data={
            "service": settings.app_name,
            "environment": settings.app_env,
            "database": serialize_database_target(settings.database_url),
        },
    )
