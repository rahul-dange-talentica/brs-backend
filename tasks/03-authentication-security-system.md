# Task 03: Authentication & Security System

**Phase**: 1 - Foundation & Core Setup  
**Sequence**: 03  
**Priority**: Critical  
**Estimated Effort**: 10-12 hours  
**Dependencies**: Task 02 (Database Models)

---

## Objective

Implement complete JWT-based authentication and security system including user registration, login, password management, and security middleware according to technical PRD specifications.

## Scope

- JWT token generation and validation
- Password hashing and verification (bcrypt)
- User registration and login endpoints
- Authentication middleware and dependencies
- Security utilities and password management
- Token refresh mechanism
- CORS and security headers configuration

## Technical Requirements

### Authentication Flow (from Technical PRD)
1. User registers/logs in with email/password
2. Server validates credentials and returns JWT access token
3. Client includes token in Authorization header for subsequent requests
4. Server validates JWT signature and expiration on each request

### Security Measures (from Technical PRD)
- **Password Security**: bcrypt hashing with salt rounds ≥ 12
- **JWT Security**: Short-lived access tokens (15 minutes), RS256 or HS256
- **Input Validation**: Pydantic models for all requests
- **CORS**: Configured for frontend domain only

## Acceptance Criteria

### ✅ Password Security
- [ ] bcrypt password hashing with salt rounds ≥ 12
- [ ] Password strength validation
- [ ] Secure password verification
- [ ] No plain text password storage or logging

### ✅ JWT Implementation
- [ ] JWT token generation with user claims
- [ ] Token validation and expiration checking
- [ ] Secure signing algorithm (HS256 with strong secret)
- [ ] Token refresh mechanism (optional for MVP)
- [ ] Access token expiration (15 minutes as per PRD)

### ✅ Authentication Endpoints
- [ ] POST /auth/register - User registration
- [ ] POST /auth/login - User authentication
- [ ] POST /auth/refresh - Token refresh (optional)
- [ ] DELETE /auth/logout - Token invalidation (client-side)

### ✅ Security Middleware
- [ ] Authentication dependency for protected routes
- [ ] Current user extraction from JWT
- [ ] Proper error handling for authentication failures
- [ ] CORS middleware configuration

### ✅ Input Validation
- [ ] Registration request validation (email, password strength)
- [ ] Login request validation
- [ ] Proper error messages without information leakage
- [ ] Email format validation

## Implementation Details

### Core Security Module (app/core/security.py)
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt rounds >= 12"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
```

### Authentication Module (app/core/auth.py)
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.security import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Authentication API Routes (app/api/auth.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### Authentication Schemas (app/schemas/auth.py)
```python
from pydantic import BaseModel, EmailStr, validator
import re

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str = None
```

### Security Configuration Update (app/main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.api import auth

app = FastAPI(
    title="Book Review System API",
    description="Backend API for Book Review Platform",
    version="1.0.0",
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.brs.example.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # Configure in settings
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
```

## Testing

### Authentication Flow Tests
- [ ] User registration with valid data
- [ ] Registration with existing email (should fail)
- [ ] User login with correct credentials
- [ ] Login with incorrect credentials (should fail)
- [ ] Login with inactive user (should fail)

### JWT Token Tests
- [ ] Token generation with correct claims
- [ ] Token validation with valid token
- [ ] Token validation with expired token (should fail)
- [ ] Token validation with invalid signature (should fail)
- [ ] Token validation with malformed token (should fail)

### Password Security Tests
- [ ] Password hashing produces different hashes for same password
- [ ] Password verification works correctly
- [ ] Password strength validation
- [ ] Bcrypt salt rounds >= 12

### Security Middleware Tests
- [ ] Protected endpoints require authentication
- [ ] Valid token allows access
- [ ] Invalid/missing token denies access
- [ ] User extraction from token works correctly

## API Testing Examples
```bash
# Register new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123","first_name":"Test","last_name":"User"}'

# Login user
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123"

# Use token for authenticated request
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Definition of Done

- [ ] All authentication endpoints implemented and tested
- [ ] JWT token generation and validation working
- [ ] Password security with bcrypt (salt rounds ≥ 12)
- [ ] Authentication middleware protecting routes
- [ ] Input validation with proper error messages
- [ ] Security configuration updated in main app
- [ ] Comprehensive test suite (80%+ coverage)
- [ ] No security vulnerabilities in authentication flow
- [ ] Token expiration working correctly (15 minutes)
- [ ] CORS properly configured

## Next Steps

After completion, this task enables:
- **Task 04**: User Management API (authentication required)
- All subsequent protected API endpoints
- User-specific operations and data access

## Notes

- Follow OWASP security best practices
- Never log passwords or tokens
- Use environment variables for secrets
- Test with various attack vectors
- Document security considerations
