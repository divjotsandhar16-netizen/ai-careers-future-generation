from pydantic import BaseModel, EmailStr, Field


class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    captcha_id: str
    captcha_answer: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    captcha_id: str | None = None
    captcha_answer: str | None = None


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=8)
    channel: str = "email"


class ResendOTPRequest(BaseModel):
    email: EmailStr
    channel: str = "email"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class GoogleAuthRequest(BaseModel):
    email: EmailStr
    name: str = "Google User"
    google_token: str = Field(min_length=6)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    is_email_verified: bool
    is_phone_verified: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    dev_otp: str | None = None
