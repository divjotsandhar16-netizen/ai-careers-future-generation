import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_captcha,
    get_current_user,
    hash_password,
    rate_limit,
    verify_captcha,
    verify_password,
)
from app.db.session import get_db
from app.models.career import OTPChallenge, User
from app.schemas.auth import (
    AuthResponse,
    CaptchaResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    OTPVerifyRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    SignupRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        is_email_verified=user.is_email_verified,
        is_phone_verified=user.is_phone_verified,
    )


def create_otp(db: Session, user: User, channel: str = "email") -> str:
    otp = f"{random.randint(100000, 999999)}"
    challenge = OTPChallenge(
        user_id=user.id,
        channel=channel,
        destination=user.email if channel == "email" else (user.phone or ""),
        otp_hash=hash_password(otp),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(challenge)
    db.commit()
    return otp


@router.get("/captcha", response_model=CaptchaResponse)
def captcha():
    return create_captcha()


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    rate_limit(f"signup:{payload.email}", 5)
    verify_captcha(payload.captcha_id, payload.captcha_answer)
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    otp = create_otp(db, user, "email")
    return AuthResponse(access_token=create_access_token(user), user=serialize_user(user), dev_otp=otp if settings.dev_auth_mode else None)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    rate_limit(f"login:{payload.email}", 10)
    if payload.captcha_id and payload.captcha_answer:
        verify_captcha(payload.captcha_id, payload.captcha_answer)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return AuthResponse(access_token=create_access_token(user, payload.remember_me), user=serialize_user(user))


@router.post("/google", response_model=AuthResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    rate_limit(f"google:{payload.email}", 10)
    # Demo-safe placeholder: production should verify google_token with Google.
    if len(payload.google_token) < 6:
        raise HTTPException(status_code=401, detail="Invalid Google token.")
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        user = User(
            name=payload.name,
            email=payload.email.lower(),
            phone=None,
            password_hash=hash_password(f"google:{payload.google_token}"),
            is_email_verified=True,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return AuthResponse(access_token=create_access_token(user, True), user=serialize_user(user))


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    challenge = (
        db.query(OTPChallenge)
        .filter(OTPChallenge.user_id == user.id, OTPChallenge.channel == payload.channel, OTPChallenge.is_used.is_(False))
        .order_by(OTPChallenge.id.desc())
        .first()
    )
    if not challenge or datetime.utcnow() > challenge.expires_at:
        raise HTTPException(status_code=400, detail="OTP expired. Resend a new code.")
    if challenge.attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many OTP attempts.")
    challenge.attempts += 1
    if not verify_password(payload.otp, challenge.otp_hash):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    challenge.is_used = True
    if payload.channel == "phone":
        user.is_phone_verified = True
    else:
        user.is_email_verified = True
    db.commit()
    return AuthResponse(access_token=create_access_token(user), user=serialize_user(user))


@router.post("/resend-otp")
def resend_otp(payload: ResendOTPRequest, db: Session = Depends(get_db)):
    rate_limit(f"otp:{payload.email}", 3, 120)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    otp = create_otp(db, user, payload.channel)
    return {"message": "OTP sent.", "dev_otp": otp if settings.dev_auth_mode else None}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    rate_limit(f"forgot:{payload.email}", 3, 120)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        return {"message": "If this email exists, a reset OTP has been sent."}
    otp = create_otp(db, user, "reset")
    return {"message": "If this email exists, a reset OTP has been sent.", "dev_otp": otp if settings.dev_auth_mode else None}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    challenge = (
        db.query(OTPChallenge)
        .filter(OTPChallenge.user_id == user.id, OTPChallenge.channel == "reset", OTPChallenge.is_used.is_(False))
        .order_by(OTPChallenge.id.desc())
        .first()
    )
    if not challenge or datetime.utcnow() > challenge.expires_at or not verify_password(payload.otp, challenge.otp_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired reset OTP.")
    challenge.is_used = True
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {"message": "Password reset successful."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)
