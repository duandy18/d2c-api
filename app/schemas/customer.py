from datetime import datetime

from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    customer_code: str
    email: str | None
    phone: str | None
    display_name: str
    status: str
    registered_at: datetime
    last_login_at: datetime | None


class CustomerRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)


class CustomerLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class CustomerAuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    customer: CustomerProfile
