from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_rate_limit_service
from app.core.config import get_settings
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RefreshTokenRequest, TokenPair, UserCreate, UserRead
from app.services.auth_service import AuthService
from app.services.rate_limit_service import RateLimitService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    service = UserService(UserRepository(db))
    if await service.get_by_email(payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        )
    user = await service.create_user(payload)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
) -> TokenPair:
    settings = get_settings()
    client_ip = _client_ip(request)
    decision = await rate_limit_service.check_login(client_ip, form_data.username)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    tokens = await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )
    if tokens is None:
        decision = await rate_limit_service.record_failed_login(client_ip, form_data.username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS if not decision.allowed else status.HTTP_401_UNAUTHORIZED,
            detail="Too many login attempts. Try again later." if not decision.allowed else "Incorrect credentials.",
            headers={"Retry-After": str(decision.retry_after_seconds)} if not decision.allowed else None,
        )
    await rate_limit_service.reset_login(client_ip, form_data.username)
    response.set_cookie(
        key=settings.admin_auth_cookie_name,
        value=tokens.access_token,
        httponly=True,
        secure=settings.admin_auth_cookie_secure,
        samesite=settings.admin_auth_cookie_samesite,
        domain=settings.admin_auth_cookie_domain_effective,
        path="/",
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key=settings.admin_refresh_cookie_name,
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.admin_auth_cookie_secure,
        samesite=settings.admin_auth_cookie_samesite,
        domain=settings.admin_auth_cookie_domain_effective,
        path="/",
        max_age=settings.jwt_refresh_token_expire_minutes * 60,
    )
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    tokens = await auth_service.refresh_tokens(payload.refresh_token)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
    return tokens


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"
