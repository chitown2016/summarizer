"""
Authentication API routes
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from backend.models.auth import (
    User, UserCreate, UserUpdate, APIKey, APIKeyCreate, APIKeyUpdate,
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    ChangePasswordRequest, UserProfile
)
from backend.services.auth_service import auth_service
from backend.middleware.auth import get_current_user, get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for JWT tokens
security = HTTPBearer()


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """
    Register a new user
    """
    try:
        user = auth_service.create_user(request)
        return RegisterResponse(
            user=user,
            message="User registered successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login user and return JWT token
    """
    # Authenticate user
    user = auth_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    if request.remember:
        # Extended token for "remember me"
        access_token_expires = timedelta(days=7)
    
    access_token = auth_service.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user information
    """
    updated_user = auth_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Change user password
    """
    # Verify current password
    user = auth_service.authenticate_user(current_user.email, request.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user_update = UserUpdate(password=request.new_password)
    updated_user = auth_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password changed successfully"}


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get user profile with API keys and stats
    """
    # Get user's API keys
    api_keys = auth_service.get_user_api_keys(current_user.id)
    
    # Calculate basic stats
    stats = {
        "total_api_keys": len(api_keys),
        "active_api_keys": len([k for k in api_keys if k.status == "active"]),
        "total_usage": sum(k.usage_count for k in api_keys),
        "providers": list(set(k.provider for k in api_keys))
    }
    
    return UserProfile(
        user=current_user,
        api_keys=api_keys,
        stats=stats
    )


# API Key Management Routes

@router.get("/api-keys", response_model=list[APIKey])
async def get_user_api_keys(current_user: User = Depends(get_current_active_user)):
    """
    Get all API keys for current user
    """
    return auth_service.get_user_api_keys(current_user.id)


@router.post("/api-keys", response_model=APIKey)
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new API key for current user
    """
    try:
        return auth_service.create_api_key(current_user.id, api_key_create)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/api-keys/{key_id}", response_model=APIKey)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific API key (must belong to current user)
    """
    api_key = auth_service.get_api_key(key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Check ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return api_key


@router.put("/api-keys/{key_id}", response_model=APIKey)
async def update_api_key(
    key_id: str,
    api_key_update: APIKeyUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update API key (must belong to current user)
    """
    # Check ownership first
    existing_key = auth_service.get_api_key(key_id)
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if existing_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update the key
    updated_key = auth_service.update_api_key(key_id, api_key_update)
    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return updated_key


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete API key (must belong to current user)
    """
    # Check ownership first
    existing_key = auth_service.get_api_key(key_id)
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if existing_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete the key
    success = auth_service.delete_api_key(key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}


@router.get("/api-keys/provider/{provider}/default", response_model=APIKey)
async def get_default_api_key(
    provider: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's default API key for a specific provider
    """
    api_key = auth_service.get_user_default_api_key(current_user.id, provider)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No default API key found for provider: {provider}"
        )
    
    return api_key

