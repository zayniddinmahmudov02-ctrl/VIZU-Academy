from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.cors import ALLOWED_ORIGIN_REGEX, ALLOWED_ORIGINS
from app.core.exceptions import register_exception_handlers

# Authentication
from app.api.auth.router import router as auth_router

# Users
from app.api.users.router import router as users_router

# Learning
from app.api.languages.router import router as languages_router
from app.api.courses.router import router as courses_router
from app.api.modules.router import router as modules_router
from app.api.lessons.router import router as lessons_router
from app.api.videos.router import router as videos_router
from app.api.video_progress.router import router as video_progress_router
from app.api.vocabularies.router import router as vocabularies_router
from app.api.readings.router import router as readings_router
from app.api.reading_question import router as reading_question_router
from app.api.reading_option import router as reading_option_router
from app.api.grammar import router as grammar_router
from app.api.listening import router as listening_router
from app.api.writing import router as writing_router
from app.api.speaking import router as speaking_router

# Student
from app.api.student_progress import (
    router as student_progress_router,
)
from app.api.student_writing import (
    router as student_writing_router,
)
from app.api.student_speaking import (
    router as student_speaking_router,
)
from app.api.student_quiz import (
    router as student_quiz_router,
)

# Quiz
from app.api.quiz import router as quiz_router
from app.api.quiz_question import (
    router as quiz_question_router,
)
from app.api.quiz_option import (
    router as quiz_option_router,
)

# Homework
from app.api.homework import (
    router as homework_router,
)

# Books
from app.api.books.router import router as books_router

# Notifications
from app.api.notifications import (
    router as notifications_router,
)

# Enrollment
from app.api.enrollment import (
    router as enrollment_router,
)

# Certificate
from app.api.v1.certificate.router import (
    router as certificate_router,
)

# Assessment Engine (universal — Course + Preparation + Mock Test)
from app.api.assessment_engine.router import (
    router as assessment_engine_router,
)

# Payment
from app.api.payment import (
    router as payment_router,
)

# Dashboard
from app.api.dashboard import (
    router as dashboard_router,
)

# Exam
from app.api.exam import (
    router as exam_router,
)
from app.api.exam.provider_router import router as exam_provider_router

# Media Library
from app.api.media_library.router import router as media_library_router

# Mock Exam System
from app.api.mock_exam.hierarchy_router import router as mock_exam_hierarchy_router
from app.api.mock_exam.content_router import router as mock_exam_content_router
from app.api.mock_exam.attempt_router import router as mock_exam_attempt_router
from app.api.mock_exam.analytics_router import router as mock_exam_analytics_router
from app.api.mock_exam.public_router import router as mock_exam_public_router

# Upload
from app.api.upload import (
    router as upload_router,
)

# Admin
from app.api.admin import (
    router as admin_router,
)
from app.api.admin.users_router import (
    router as admin_users_router,
)
from app.api.admin.vizu_pay_router import (
    router as admin_vizu_pay_router,
)
from app.api.admin.videos_router import (
    router as admin_videos_router,
)
from app.api.admin.ai_content_router import (
    router as admin_ai_content_router,
)
from app.api.admin.quiz_generation_router import (
    router as admin_quiz_generation_router,
)
from app.api.admin.books_router import (
    router as admin_books_router,
)

# VIZU Pay
from app.api.vizu_pay import (
    router as vizu_pay_router,
)

# Health
from app.api.health import (
    router as health_router,
)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

register_exception_handlers(app)

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    # Local dev origins are always allowed (any port) via the regex below.
    # Production frontend domain(s) come from CORS_ALLOWED_ORIGINS in the
    # environment — never hardcoded, since a frontend served from a real
    # domain would otherwise be silently rejected by the browser's CORS
    # check on every API call.
    #
    # Sourced from app.core.cors so the exception handlers (which
    # CORSMiddleware does NOT wrap) can apply the exact same allow-list to
    # error responses — see core/cors.py for why that matters.
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX.pattern,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ==================================================
# ROUTERS
# ==================================================
#
# Phase 5.4 — Enterprise API Standardization. Every router below is
# mounted TWICE:
#
#   1. At its original bare prefix (e.g. /auth) — preserved, unchanged,
#      for backward compatibility. Nothing that already depends on these
#      paths (direct-to-backend callers bypassing the public gateway,
#      external integrations, etc.) breaks.
#   2. Under /api/v1 (e.g. /api/v1/auth) — the new, official, standardized
#      API surface. This is what nginx's API Gateway proxies and what all
#      frontend code now calls. /api/v1/certificates already used this
#      pattern from the start; every router now follows the same rule,
#      with no exceptions.
#
# Both mounts point at the exact same router object — no endpoint, path
# operation, or business logic is duplicated or diverges between them.

_ALL_ROUTERS = [
    auth_router,
    users_router,
    languages_router,
    courses_router,
    modules_router,
    lessons_router,
    videos_router,
    video_progress_router,
    vocabularies_router,
    readings_router,
    reading_question_router,
    reading_option_router,
    grammar_router,
    listening_router,
    writing_router,
    speaking_router,
    student_progress_router,
    student_writing_router,
    student_speaking_router,
    student_quiz_router,
    quiz_router,
    quiz_question_router,
    quiz_option_router,
    homework_router,
    books_router,
    notifications_router,
    enrollment_router,
    payment_router,
    dashboard_router,
    exam_router,
    exam_provider_router,
    media_library_router,
    mock_exam_hierarchy_router,
    mock_exam_content_router,
    mock_exam_attempt_router,
    mock_exam_analytics_router,
    mock_exam_public_router,
    upload_router,
    admin_router,
    admin_users_router,
    admin_vizu_pay_router,
    admin_videos_router,
    admin_ai_content_router,
    admin_quiz_generation_router,
    admin_books_router,
    vizu_pay_router,
    assessment_engine_router,
    health_router,
]

# 1. Legacy bare mounts — preserved exactly as before.
for _router in _ALL_ROUTERS:
    app.include_router(_router)

# certificate_router has never had a bare mount — /api/v1/certificates was
# always its only address, already compliant with the standard below.
app.include_router(certificate_router, prefix=settings.API_V1_PREFIX)

# 2. Standardized /api/v1 mounts — the official API surface going forward.
for _router in _ALL_ROUTERS:
    app.include_router(_router, prefix=settings.API_V1_PREFIX)

# ==================================================
# STATIC FILES
# ==================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory="uploads",
    ),
    name="uploads",
)

# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():

    return {
        "status": "running",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }