"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    Token, 
    TokenRefresh,
    LoginResponse,
    UserResponse,
    PasswordChangeRequest
)
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.auth import get_current_active_user
from app.config import settings
from app.schemas.common import create_success_response

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register new user account.
    
    Creates a new user account with email and password validation.
    Returns access token and user information upon successful registration.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email.lower(),
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}, 
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
        updated_at=new_user.updated_at.isoformat()
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response
    )


@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Uses OAuth2 password flow for authentication.
    Username field should contain the email address.
    """
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has been deactivated. Please contact support."
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response
    )


@router.post("/login/json", response_model=LoginResponse)
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user with JSON payload and return access token.
    
    Alternative login endpoint that accepts JSON payload instead of form data.
    """
    user = db.query(User).filter(User.email == user_data.email.lower()).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has been deactivated. Please contact support."
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Validates refresh token and returns new access token if valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token_data.refresh_token)
        if payload is None:
            raise credentials_exception
        
        # Check if it's a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Requires current password for verification and validates new password strength.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update user password
    current_user.password_hash = new_password_hash
    db.commit()
    
    return create_success_response(
        data={"user_id": str(current_user.id), "updated_at": "2024-01-01T12:00:00Z"},
        message="Password updated successfully"
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout user (client-side token invalidation).
    
    Since we're using stateless JWT tokens, actual logout is handled client-side
    by removing the token. This endpoint serves as a confirmation.
    """
    return create_success_response(
        data={"user_id": str(current_user.id), "logged_out_at": "2024-01-01T12:00:00Z"},
        message="Successfully logged out"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Returns user profile data for the authenticated user.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat()
    )
