from pydantic import BaseModel


class LoginIn(BaseModel):
    # ponytail: plain str, not EmailStr — LAN domains like `admin@smartcampus.local`
    # are reserved TLDs that email-validator rejects. Emails are validated at creation (P1).
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    force_password_reset: bool = False


class RefreshIn(BaseModel):
    refresh_token: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str
