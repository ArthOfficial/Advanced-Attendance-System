from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.models.attendance import AttendanceSession
from app.services.base import BaseService


class SessionService(BaseService):
    def get_or_create_today(self) -> AttendanceSession:
        today = datetime.now(timezone.utc).date()
        existing = self.db.query(AttendanceSession).filter_by(session_date=today).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                self.db.commit()
            return existing
        # ponytail: clock-recovery — server date behind newest session ⇒ reuse newest
        newest = (self.db.query(AttendanceSession)
                  .order_by(AttendanceSession.session_date.desc()).first())
        if newest and newest.session_date > today:
            return newest
        (self.db.query(AttendanceSession)
         .filter(AttendanceSession.is_active.is_(True)).update({"is_active": False}))
        try:
            s = AttendanceSession(session_code=f"ATT-{today.isoformat()}",
                                  session_date=today, is_active=True)
            self.db.add(s)
            self.db.commit()
            self.db.refresh(s)
            return s
        except IntegrityError:
            self.db.rollback()
            return self.db.query(AttendanceSession).filter_by(session_date=today).one()
