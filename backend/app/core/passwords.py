from datetime import date


def dob_password(d: date) -> str:
    return d.strftime("%d%m%Y")
