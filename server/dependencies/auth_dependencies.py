import os
from fastapi import Depends, HTTPException, Request
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from server.backend.database import get_session
from server.repositories.user import UserRepository
from server.schemas.user import UserOut

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


async def get_current_user_from_cookie(
        request: Request,
        db: AsyncSession = Depends(get_session)
) -> UserOut:
    """
    Get the current user from the access token cookie or Authorization header.
    If no valid token is provided, raises a 401 Unauthorized exception.
    """
    access_token = request.cookies.get("access_token")

    if not access_token:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            access_token = authorization.replace("Bearer ", "")

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
