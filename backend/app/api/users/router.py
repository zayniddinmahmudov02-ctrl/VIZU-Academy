from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User

from app.schemas.auth.user import (
    ChangePasswordRequest,
    LanguageUpdateRequest,
    ProfileUpdateRequest,
    UserResponse,
)

from app.services.auth.service import (
    change_password as change_password_service,
    remove_profile_image,
    set_profile_image,
    update_preferred_language,
    update_profile,
)
from app.services.upload import UploadService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# Avatar-specific limits — kept local to this router (same pattern as the
# vizu_pay proof-of-payment upload) rather than a new global config knob.
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_profile(db, current_user, data)


@router.put("/me/password")
async def change_my_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = change_password_service(
        db,
        current_user,
        data.current_password,
        data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    return {"message": "Password changed successfully."}


@router.put("/me/language", response_model=UserResponse)
async def update_my_language(
    data: LanguageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_preferred_language(db, current_user, data.language)


@router.post("/me/photo", response_model=UserResponse)
async def upload_my_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported image type '{file.content_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))}"
            ),
        )

    contents = await file.read()

    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds the maximum upload size of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    await file.seek(0)

    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }[file.content_type]

    # Unique per-upload filename — avatars share one folder across every
    # user, so reusing the client's original filename risks two users'
    # photos colliding on disk.
    file.filename = f"{uuid4().hex}.{extension}"

    old_image = current_user.profile_image

    result = await UploadService().upload(file, "avatars")

    user = set_profile_image(db, current_user, result["url"])

    if old_image:
        await _delete_uploaded_image(old_image)

    return user


@router.delete("/me/photo", response_model=UserResponse)
async def delete_my_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    old_image = current_user.profile_image

    user = remove_profile_image(db, current_user)

    if old_image:
        await _delete_uploaded_image(old_image)

    return user


async def _delete_uploaded_image(url: str) -> None:
    """Best-effort cleanup of the previous avatar file. Never raises —
    a missing/already-gone file must not fail the request that's
    replacing or removing it."""

    prefix = "/uploads/"

    if not url.startswith(prefix):
        return

    try:
        await UploadService().delete(url[len(prefix):])
    except OSError:
        pass
