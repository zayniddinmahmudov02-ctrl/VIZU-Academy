from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, field_validator, model_validator

from app.schemas.base import BaseSchema
from app.services.advertisement_validation import validate_image_url, validate_target_url


class AdvertisementPublic(BaseSchema):
    """What a student's dashboard receives — no analytics, no admin data.
    `target_url` is NOT exposed; the banner links to the tracking redirect."""

    id: UUID
    title: str
    description: str | None
    image_url: str | None
    cta_text: str
    click_path: str


class _AdvertisementFields(BaseSchema):
    @field_validator("title", check_fields=False)
    @classmethod
    def _title(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Titel darf nicht leer sein.")
        return value

    @field_validator("target_url", check_fields=False)
    @classmethod
    def _target(cls, value):
        return validate_target_url(value) if value is not None else value

    @field_validator("image_url", check_fields=False)
    @classmethod
    def _image(cls, value):
        return validate_image_url(value)

    @field_validator("cta_text", check_fields=False)
    @classmethod
    def _cta(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or "Mehr erfahren"

    @model_validator(mode="after")
    def _dates(self):
        starts, ends = getattr(self, "starts_at", None), getattr(self, "ends_at", None)
        if starts and ends and ends <= starts:
            raise ValueError("Enddatum muss nach dem Startdatum liegen.")
        return self


class AdvertisementCreate(_AdvertisementFields):
    title: str
    description: str | None = None
    image_url: str | None = None
    target_url: str
    cta_text: str = "Mehr erfahren"
    is_active: bool = False
    priority: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AdvertisementUpdate(_AdvertisementFields):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    target_url: str | None = None
    cta_text: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AdvertisementAdmin(BaseSchema):
    id: UUID
    title: str
    description: str | None
    image_url: str | None
    target_url: str
    cta_text: str
    is_active: bool
    priority: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime
    impressions: int
    clicks: int
    ctr: float
    # Whether this ad is the one students currently see on the dashboard.
    is_current: bool
    model_config = ConfigDict(from_attributes=True)


class AdvertisementSeriesPoint(BaseSchema):
    date: str
    impressions: int
    clicks: int


class AdvertisementAnalytics(BaseSchema):
    advertisement_id: UUID
    impressions: int
    clicks: int
    ctr: float
    impressions_today: int
    clicks_today: int
    impressions_week: int
    clicks_week: int
    series: list[AdvertisementSeriesPoint]


class ImpressionResult(BaseSchema):
    counted: bool
