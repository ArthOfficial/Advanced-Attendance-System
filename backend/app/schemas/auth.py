from pydantic import BaseModel


class LoginIn(BaseModel):
    # ponytail: plain str — employee IDs and `.local` LAN emails both land here.
    # Emails are validated at teacher/admin creation, not at login.
    identifier: str
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
