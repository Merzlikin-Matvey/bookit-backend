from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from server.backend.database import get_session
from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.models.user import User
from server.services.image_storage import ImageStorage

router = APIRouter(tags=["avatar"], prefix="/avatar")
image_storage = ImageStorage()


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user_from_cookie),
        db: Session = Depends(get_session)
):
    """Upload a new avatar for the current user"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        image_id = image_storage.upload_image(file)

        current_user.avatar_id = image_id
        await db.commit()

        return {"avatar_id": image_id}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_avatar(user: User = Depends(get_current_user_from_cookie)):
    try:
        image_id = user.avatar_id
        image_data = image_storage.get_image(image_id)

        return Response(
            content=image_data,
            media_type="image/jpeg"
        )

    except Exception:
        try:
            image_id = "default_avatar"
            image_data = image_storage.get_image(image_id)

            return Response(
                content=image_data,
                media_type="image/jpeg"
            )
        except Exception:
            raise HTTPException(status_code=404, detail="Avatar not found")
