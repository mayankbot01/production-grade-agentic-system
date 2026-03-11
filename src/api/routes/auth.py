from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from src.data.schemas.auth import UserCreate, UserResponse, Token
from src.services.database import DatabaseService, get_db
from src.utils.auth import create_access_token, verify_token
from src.utils.sanitization import sanitize_string, sanitize_email, validate_password
from passlib.context import CryptContext
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: DatabaseService = Depends(get_db)):
    """Register a new user."""
    username = sanitize_string(user_data.username)
    email = sanitize_email(user_data.email)

    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with letters and numbers"
        )

    existing = await db.get_user_by_username(username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    hashed = hash_password(user_data.password)
    user = await db.create_user(username=username, email=email, hashed_password=hashed)
    logger.info(f"New user registered: {username}")
    return UserResponse(id=user["id"], username=user["username"], email=user["email"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseService = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    user = await db.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user["username"])
    logger.info(f"User logged in: {user['username']}")
    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(verify_token), db: DatabaseService = Depends(get_db)):
    """Get current authenticated user info."""
    user = await db.get_user_by_username(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=user["id"], username=user["username"], email=user["email"])
