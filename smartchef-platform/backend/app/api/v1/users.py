from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission
from app.models.user import User, Role

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user_management")),
):
    result = await db.execute(
        select(User, Role.name.label("role_name"))
        .outerjoin(Role, User.role_id == Role.id)
        .order_by(User.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "display_name": u.display_name,
            "role_name": role_name,
            "is_active": u.is_active,
        }
        for u, role_name in rows
    ]
