from contextlib import asynccontextmanager
import os
import shutil
import tempfile
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Post, User, create_db_and_tables, get_async_session
from app.schemas import UserCreate, UserRead, UserUpdate
from app.images import imagekit
from app.users import auth_backend, current_active_users, fastapi_users
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
    prefix="/users",
    tags=["users"],
)


@app.get("/")
async def home():
    return {"message": "API is running"}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_users),
    session: AsyncSession = Depends(get_async_session),
):
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename or "")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        with open(temp_file_path, "rb") as uploaded_file:
            # Supports both ImageKit Python SDK API generations.
            if hasattr(imagekit, "files") and hasattr(imagekit.files, "upload"):
                upload_result = imagekit.files.upload(
                    file=uploaded_file,
                    file_name=file.filename or "uploaded_file",
                    options={
                        "use_unique_file_name": True,
                        "tags": ["backend-upload"],
                    },
                )
            else:
                upload_result = imagekit.upload_file(
                    file=uploaded_file,
                    file_name=file.filename or "uploaded_file",
                    options=UploadFileRequestOptions(
                        use_unique_file_name=True,
                        tags=["backend-upload"],
                    ),
                )

        # Newer and older SDK responses do not expose exactly the same metadata.
        metadata = getattr(upload_result, "response_metadata", None)
        status_code = getattr(metadata, "http_status_code", None)
        if status_code is not None and status_code not in (200, 201):
            raise HTTPException(status_code=502, detail="ImageKit upload failed")

        uploaded_url = getattr(upload_result, "url", None)
        uploaded_name = getattr(upload_result, "name", None) or file.filename or "uploaded_file"
        if not uploaded_url:
            raise HTTPException(
                status_code=502,
                detail="ImageKit did not return a file URL. Check ImageKit credentials and SDK version.",
            )

        post = Post(
            user_id=user.id,
            caption=caption,
            url=uploaded_url,
            file_type="video" if (file.content_type or "").startswith("video/") else "image",
            file_name=uploaded_name,
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)

        return {
            "id": str(post.id),
            "user_id": str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat() if post.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        # Keep the API response useful without exposing internal exception details.
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {type(exc).__name__}. Check the server terminal for details.",
        ) from exc
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        await file.close()


@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_users),
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()

    user_result = await session.execute(select(User))
    users = user_result.scalars().all()
    user_dict = {item.id: item.email for item in users}

    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "user_id": str(post.user_id) if post.user_id else None,
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "is_owner": post.user_id == user.id,
                "email": user_dict.get(post.user_id, "Unknown") if post.user_id else "Unknown",
            }
        )
    return {"posts": posts_data}


@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_users),
):
    try:
        post_uuid = uuid.UUID(post_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid post ID format")

    try:
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this post",
            )

        await session.delete(post)
        await session.commit()
        return {"success": True, "message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not delete post") from exc
