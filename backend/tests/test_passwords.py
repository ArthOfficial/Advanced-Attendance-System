from datetime import date

from app.core.passwords import dob_password


def test_dob_password_format():
    assert dob_password(date(1990, 8, 15)) == "15081990"
    assert dob_password(date(2001, 1, 5)) == "05012001"
