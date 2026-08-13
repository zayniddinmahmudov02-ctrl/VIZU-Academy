from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VideoBase(BaseSchema):
    title: str
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    order_index: int = 1
    is_preview: bool = False
    is_published: bool = False


class VideoCreate(VideoBase):
    lesson_id: UUID


class VideoUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    order_index: int | None = None
    is_preview: bool | None = None
    is_published: bool | None = None


class VideoResponse(VideoBase):
    id: UUID
    lesson_id: UUID

    # Storage keys — fine to surface here since VideoResponse is only
    # ever returned from admin-authenticated endpoints. The student
    # streaming endpoints (GET /videos/{id}, GET /videos/by-lesson/{id})
    # return VideoStreamResponse instead, which never includes these.
    storage_key: str | None = None
    thumbnail_key: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VideoStreamResponse(BaseSchema):
    """The shape returned to a student for playback — access-gated
    metadata plus a playable URL. Never the storage_key or any other
    internal field."""

    id: UUID
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    video_url: str


# ==========================
# Chunked upload
# ==========================


class VideoUploadInitRequest(BaseSchema):
    lesson_id: UUID
    title: str
    description: str | None = None
    duration_seconds: int = 0
    order_index: int = 1
    is_preview: bool = False
    is_published: bool = False
    filename: str
    content_type: str
    total_size_bytes: int
    # Set to swap an existing video's file instead of creating a new one —
    # the chunked equivalent of PUT /admin/videos/{id}/replace.
    replace_video_id: UUID | None = None


class VideoUploadInitResponse(BaseSchema):
    upload_id: UUID
    # Server-computed, not client-chosen — the frontend must slice the
    # file using exactly this size so total_chunks stays correct and no
    # single chunk request risks exceeding the edge's per-request limit.
    chunk_size_bytes: int
    total_chunks: int


class VideoUploadChunkResponse(BaseSchema):
    upload_id: UUID
    chunk_number: int
    uploaded_chunks: int
    total_chunks: int


class VideoUploadStatusResponse(BaseSchema):
    upload_id: UUID
    total_chunks: int
    uploaded_chunks: list[int]
    is_ready_to_complete: bool
