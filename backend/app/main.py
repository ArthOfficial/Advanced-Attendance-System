from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.providers.qr_provider  # noqa: F401  registers QR provider
from app.api.academic import router as academic_router
from app.api.admin import router as admin_router
from app.api.attendance import router as attendance_router
from app.api.auth import router as auth_router
from app.api.imports import router as imports_router
from app.api.kiosk_qr import router as kiosk_qr_router
from app.api.kiosks import router as kiosks_router
from app.api.teachers import router as teachers_router
from app.config import settings

app = FastAPI(title="SmartCampus Attendance", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(academic_router)
app.include_router(imports_router)  # before teachers: /teachers/import/* must not hit /teachers/{tid}
app.include_router(teachers_router)
app.include_router(kiosks_router)
app.include_router(kiosk_qr_router)
app.include_router(attendance_router)


@app.get("/health")
def health():
    return {"status": "ok"}
