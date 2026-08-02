from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
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

# Enrollment
from app.api.enrollment import (
    router as enrollment_router,
)

# Certificate
from app.api.v1.certificate.router import (
    router as certificate_router,
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *settings.cors_origins,
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ==================================================
# ROUTERS
# ==================================================

app.include_router(auth_router)

app.include_router(users_router)

app.include_router(languages_router)
app.include_router(courses_router)
app.include_router(modules_router)
app.include_router(lessons_router)
app.include_router(videos_router)
app.include_router(video_progress_router)
app.include_router(vocabularies_router)
app.include_router(readings_router)
app.include_router(reading_question_router)
app.include_router(reading_option_router)
app.include_router(grammar_router)
app.include_router(listening_router)
app.include_router(writing_router)
app.include_router(speaking_router)

app.include_router(student_progress_router)
app.include_router(student_writing_router)
app.include_router(student_speaking_router)
app.include_router(student_quiz_router)

app.include_router(quiz_router)
app.include_router(quiz_question_router)
app.include_router(quiz_option_router)

app.include_router(homework_router)

app.include_router(enrollment_router)

app.include_router(
    certificate_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(payment_router)

app.include_router(dashboard_router)

app.include_router(exam_router)
app.include_router(exam_provider_router)
app.include_router(media_library_router)

app.include_router(upload_router)

app.include_router(admin_router)
app.include_router(admin_users_router)
app.include_router(admin_vizu_pay_router)
app.include_router(admin_videos_router)
app.include_router(vizu_pay_router)

app.include_router(health_router)

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