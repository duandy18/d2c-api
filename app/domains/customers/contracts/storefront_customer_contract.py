"""Storefront customer API contracts."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CustomerProfile(BaseModel):
    customer_code: str
    email: str | None
    phone: str | None
    display_name: str
    status: str
    registered_at: datetime
    last_login_at: datetime | None


class CustomerRegisterRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def require_email_or_phone(self) -> "CustomerRegisterRequest":
        if self.email is None and self.phone is None:
            raise ValueError("customer_email_or_phone_required")
        return self


class CustomerLoginRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def require_email_or_phone(self) -> "CustomerLoginRequest":
        if self.email is None and self.phone is None:
            raise ValueError("customer_email_or_phone_required")
        return self


class CustomerAuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    customer: CustomerProfile


class CustomerLogoutResponse(BaseModel):
    status: str = "ok"



class CustomerChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class CustomerChangePasswordResponse(BaseModel):
    status: str = "ok"
