"""
Authentication API endpoints.

Provides registration, login, and current-user retrieval for business owners.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import get_current_user, TokenData
from app.services.auth_service import auth_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request / Response schemas ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Min 8 chars")
    business_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    success: bool = True
    data: dict
    message: str


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    """Register a new business account and return a JWT token."""
    try:
        business = await auth_service.register_business(
            email=body.email,
            password=body.password,
            business_name=body.business_name,
            phone=body.phone,
        )
        tokens = auth_service.create_tokens(business.business_id, body.email)
        logger.info("Business registered: %s", business.business_id)
        return AuthResponse(
            data={
                "business_id": business.business_id,
                "name": business.name,
                **tokens,
            },
            message="Registration successful",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Authenticate a business owner and return a JWT token."""
    business_data = await auth_service.authenticate(body.email, body.password)
    if not business_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens = auth_service.create_tokens(
        business_data["business_id"], business_data["owner_email"]
    )
    logger.info("Login successful: %s", business_data["business_id"])
    return AuthResponse(
        data={
            "business_id": business_data["business_id"],
            "name": business_data["name"],
            **tokens,
        },
        message="Login successful",
    )


@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    from app.core.database import MongoDB

    collection = MongoDB.get_collection("businesses")
    business = await collection.find_one(
        {"business_id": current_user.sub}, {"owner_password": 0, "_id": 0}
    )
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    return AuthResponse(data=business, message="Current user retrieved")
