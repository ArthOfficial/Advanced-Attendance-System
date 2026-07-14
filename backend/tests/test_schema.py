import sqlalchemy as sa

from app.database import engine

EXPECTED = {
    "users", "faculties", "departments", "teachers", "attendance_kiosks", "devices",
    "attendance_sessions", "attendance", "qr_tokens", "audit_logs", "system_settings",
    "face_profiles", "face_embeddings", "face_verification_logs",
}


def test_all_tables_exist():
    # Requires: alembic upgrade head already run against the test DB.
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED <= tables, f"missing: {EXPECTED - tables}"
