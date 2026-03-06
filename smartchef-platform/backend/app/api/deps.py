from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import decode_access_token
from app.services.auth_service import get_user_by_id

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效Token")
    user = await get_user_by_id(db, UUID(user_id))
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    return user


def require_permission(permission_key: str):
    async def checker(current_user=Depends(get_current_user)):
        if not current_user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无角色分配")
        permissions = current_user.role.permissions or {}

        parts = permission_key.split(".")
        value = permissions
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                break

        if not value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"无权限: {permission_key}")
        return current_user

    return checker
