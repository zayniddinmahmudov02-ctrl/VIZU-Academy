from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, field_validator, model_validator

from app.schemas.base import BaseSchema
from app.services.advertisement_validation import validate_image_url, validate_target_url


LinkType = Literal["EXTERNAL", "INTERNAL"]


class AdvertisementPublic(BaseSchema):
    """What a student's dashboard receives — no analytics, no admin data.
    `target_url` is NOT exposed; an external banner links to the tracking
    redirect, an internal one navigates in the app to `internal_path` (always
    a whitelisted student page, see app.services.student_routes) and reports
    the click with POST click_path."""

    id: UUID
    title: str
    description: str | None
    image_url: str | None
    cta_text: str
    click_path: str
    link_type: LinkType = "EXTERNAL"
    internal_path: str | None = None


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
    link_type: LinkType = "EXTERNAL"
    # EXTERNAL: required, validated http(s) URL
    target_url: str | None = None
    # INTERNAL: a key of app.services.student_routes + its whitelisted params
    internal_route: str | None = None
    internal_params: dict[str, str] | None = None
    cta_text: str = "Mehr erfahren"
    is_active: bool = False
    priority: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def _link(self):
        apply_link_rules(self.__dict__)
        return self


def apply_link_rules(values: dict) -> None:
    """Make the link fields consistent (in place) or raise ValueError:
    EXTERNAL needs a target_url and has no internal route; INTERNAL needs a
    registered student page with valid params and has no target_url."""
    from app.services import student_routes

    if values.get("link_type") == "INTERNAL":
        values["internal_params"] = student_routes.validate(values.get("internal_route"), values.get("internal_params"))
        values["target_url"] = None
    else:
        if not values.get("target_url"):
            raise ValueError("Link fehlt — bitte eine vollständige http(s)-Adresse eingeben.")
        values["internal_route"] = None
        values["internal_params"] = None


class AdvertisementUpdate(_AdvertisementFields):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    link_type: LinkType | None = None
    target_url: str | None = None
    internal_route: str | None = None
    internal_params: dict[str, str] | None = None
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
    link_type: LinkType
    target_url: str | None
    internal_route: str | None
    internal_params: dict[str, str] | None
    # resolved student page (internal) and whether the stored route is still
    # valid — false: the page was removed, students are sent to the fallback
    internal_path: str | None
    link_valid: bool
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


class ClickResult(BaseSchema):
    counted: bool


class InternalRouteParam(BaseSchema):
    name: str
    choices: list[str]


class InternalRoute(BaseSchema):
    key: str
    group: str
    label: str
    path: str
    params: list[InternalRouteParam]
