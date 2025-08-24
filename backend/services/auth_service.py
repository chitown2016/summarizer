"""
Authentication service for user management and JWT token handling
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet

from backend.models.auth import User, UserCreate, UserUpdate, APIKey, APIKeyCreate, APIKeyUpdate, UserRole, APIKeyStatus


class AuthService:
    """Core authentication service"""
    
    def __init__(self):
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT settings
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Encryption for API keys
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "your-32-byte-encryption-key-change-this-in-production")
        # Ensure the key is properly formatted for Fernet
        if len(self.encryption_key) != 44:  # Fernet key length
            # Generate a proper Fernet key if the current one is invalid
            from cryptography.fernet import Fernet as FernetGenerator
            self.encryption_key = FernetGenerator.generate_key().decode()
        self.cipher_suite = Fernet(self.encryption_key.encode())
        
        # Data storage paths
        self.data_dir = Path("data")
        self.users_file = self.data_dir / "users.json"
        self.api_keys_file = self.data_dir / "api_keys.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data files
        self._init_data_files()
    
    def _init_data_files(self):
        """Initialize data files if they don't exist"""
        if not self.users_file.exists():
            self.users_file.write_text("[]")
        
        if not self.api_keys_file.exists():
            self.api_keys_file.write_text("[]")
    
    def _load_users(self) -> list:
        """Load users from JSON file"""
        try:
            data = json.loads(self.users_file.read_text())
            # Convert datetime strings back to datetime objects
            for user in data:
                for key in ['created_at', 'updated_at', 'last_login']:
                    if user.get(key) and isinstance(user[key], str):
                        try:
                            user[key] = datetime.fromisoformat(user[key].replace('Z', '+00:00'))
                        except ValueError:
                            # If parsing fails, keep as string
                            pass
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_users(self, users: list):
        """Save users to JSON file"""
        self.users_file.write_text(json.dumps(users, indent=2, default=str))
    
    def _load_api_keys(self) -> list:
        """Load API keys from JSON file"""
        try:
            return json.loads(self.api_keys_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_api_keys(self, api_keys: list):
        """Save API keys to JSON file"""
        self.api_keys_file.write_text(json.dumps(api_keys, indent=2, default=str))
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self._load_users()
        for user_data in users:
            if user_data.get("email") == email:
                return User(**user_data)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self._load_users()
        for user_data in users:
            if user_data.get("id") == user_id:
                return User(**user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self._load_users()
        for user_data in users:
            if user_data.get("username") == username:
                return User(**user_data)
        return None
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if email already exists
        if self.get_user_by_email(user_create.email):
            raise ValueError("Email already registered")
        
        # Check if username already exists
        if self.get_user_by_username(user_create.username):
            raise ValueError("Username already taken")
        
        # Create user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_data = {
            "id": user_id,
            "email": user_create.email,
            "username": user_create.username,
            "full_name": user_create.full_name,
            "hashed_password": self.get_password_hash(user_create.password),
            "role": UserRole.USER,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_login": None
        }
        
        # Save to file
        users = self._load_users()
        users.append(user_data)
        self._save_users(users)
        
        # Return user without password
        return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        # Load users and find the one with matching email
        users = self._load_users()
        for user_data in users:
            if user_data.get("email") == email:
                # Verify password
                if not self.verify_password(password, user_data["hashed_password"]):
                    return None
                
                # Update last login
                user_data["last_login"] = datetime.utcnow()
                user_data["updated_at"] = datetime.utcnow()
                self._save_users(users)
                
                # Return user without password
                return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
        
        return None
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        users = self._load_users()
        
        for i, user_data in enumerate(users):
            if user_data.get("id") == user_id:
                # Update fields
                update_data = user_update.dict(exclude_unset=True)
                
                # Hash password if provided
                if "password" in update_data:
                    update_data["hashed_password"] = self.get_password_hash(update_data.pop("password"))
                
                # Update timestamp
                update_data["updated_at"] = datetime.utcnow()
                
                # Apply updates
                user_data.update(update_data)
                self._save_users(users)
                
                # Return updated user without password
                return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
        
        return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        users = self._load_users()
        api_keys = self._load_api_keys()
        
        # Remove user
        original_length = len(users)
        users = [u for u in users if u.get("id") != user_id]
        
        if len(users) < original_length:
            # Remove user's API keys
            api_keys = [k for k in api_keys if k.get("user_id") != user_id]
            
            self._save_users(users)
            self._save_api_keys(api_keys)
            return True
        
        return False
    
    def get_user_api_keys(self, user_id: str) -> list[APIKey]:
        """Get all API keys for a user"""
        api_keys_data = self._load_api_keys()
        user_keys = []
        
        for key_data in api_keys_data:
            if key_data.get("user_id") == user_id:
                # Decrypt API key for display (masked)
                encrypted_key = key_data.get("encrypted_api_key", "")
                if encrypted_key:
                    try:
                        decrypted_key = self._decrypt_api_key(encrypted_key)
                        # Mask the key for display
                        masked_key = decrypted_key[:8] + "*" * (len(decrypted_key) - 12) + decrypted_key[-4:]
                        key_data["api_key"] = masked_key
                    except Exception:
                        key_data["api_key"] = "***ERROR***"
                
                user_keys.append(APIKey(**key_data))
        
        return user_keys
    
    def create_api_key(self, user_id: str, api_key_create: APIKeyCreate) -> APIKey:
        """Create a new API key for user"""
        # Check if user exists
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # If this is the default key, unset other defaults for this provider
        if api_key_create.is_default:
            self._unset_default_keys(user_id, api_key_create.provider)
        
        # Create API key
        key_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        key_data = {
            "id": key_id,
            "user_id": user_id,
            "name": api_key_create.name,
            "provider": api_key_create.provider,
            "encrypted_api_key": self._encrypt_api_key(api_key_create.api_key),
            "is_default": api_key_create.is_default,
            "status": APIKeyStatus.ACTIVE,
            "created_at": now,
            "updated_at": now,
            "last_used": None,
            "usage_count": 0
        }
        
        # Save to file
        api_keys = self._load_api_keys()
        api_keys.append(key_data)
        self._save_api_keys(api_keys)
        
        # Return API key with masked key
        return APIKey(**{**key_data, "api_key": api_key_create.api_key[:8] + "*" * (len(api_key_create.api_key) - 12) + api_key_create.api_key[-4:]})
    
    def _unset_default_keys(self, user_id: str, provider: str):
        """Unset default flag for other keys of the same provider"""
        api_keys = self._load_api_keys()
        
        for key_data in api_keys:
            if (key_data.get("user_id") == user_id and 
                key_data.get("provider") == provider and 
                key_data.get("is_default")):
                key_data["is_default"] = False
                key_data["updated_at"] = datetime.utcnow()
        
        self._save_api_keys(api_keys)
    
    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID"""
        api_keys = self._load_api_keys()
        
        for key_data in api_keys:
            if key_data.get("id") == key_id:
                # Decrypt and return full key
                encrypted_key = key_data.get("encrypted_api_key", "")
                if encrypted_key:
                    try:
                        decrypted_key = self._decrypt_api_key(encrypted_key)
                        key_data["api_key"] = decrypted_key
                    except Exception:
                        return None
                
                return APIKey(**key_data)
        
        return None
    
    def get_user_default_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """Get user's default API key for a provider - returns the decrypted API key string"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Looking for API key for user_id: {user_id}, provider: {provider}")
        
        api_keys = self._load_api_keys()
        logger.info(f"Loaded {len(api_keys)} API keys from database")
        
        for key_data in api_keys:
            logger.info(f"Checking key: user_id={key_data.get('user_id')}, provider={key_data.get('provider')}, is_default={key_data.get('is_default')}, status={key_data.get('status')}")
            
            if (key_data.get("user_id") == user_id and 
                key_data.get("provider") == provider and 
                key_data.get("is_default") and
                key_data.get("status") == APIKeyStatus.ACTIVE):
                
                logger.info(f"Found matching API key: {key_data.get('id')}")
                
                # Decrypt and return the API key string
                encrypted_key = key_data.get("encrypted_api_key", "")
                if encrypted_key:
                    try:
                        decrypted_key = self._decrypt_api_key(encrypted_key)
                        logger.info("Successfully decrypted API key")
                        return decrypted_key
                    except Exception as e:
                        logger.error(f"Failed to decrypt API key: {e}")
                        return None
                else:
                    logger.warning("No encrypted API key found in key data")
                    return None
        
        logger.warning(f"No matching API key found for user_id: {user_id}, provider: {provider}")
        return None
    
    def update_api_key(self, key_id: str, api_key_update: APIKeyUpdate) -> Optional[APIKey]:
        """Update API key"""
        api_keys = self._load_api_keys()
        
        for i, key_data in enumerate(api_keys):
            if key_data.get("id") == key_id:
                # Update fields
                update_data = api_key_update.dict(exclude_unset=True)
                
                # Encrypt API key if provided
                if "api_key" in update_data:
                    update_data["encrypted_api_key"] = self._encrypt_api_key(update_data.pop("api_key"))
                
                # If setting as default, unset other defaults
                if update_data.get("is_default"):
                    self._unset_default_keys(key_data["user_id"], key_data["provider"])
                
                # Update timestamp
                update_data["updated_at"] = datetime.utcnow()
                
                # Apply updates
                key_data.update(update_data)
                self._save_api_keys(api_keys)
                
                # Return updated API key with masked key
                encrypted_key = key_data.get("encrypted_api_key", "")
                if encrypted_key:
                    try:
                        decrypted_key = self._decrypt_api_key(encrypted_key)
                        masked_key = decrypted_key[:8] + "*" * (len(decrypted_key) - 12) + decrypted_key[-4:]
                        key_data["api_key"] = masked_key
                    except Exception:
                        key_data["api_key"] = "***ERROR***"
                
                return APIKey(**key_data)
        
        return None
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete API key"""
        api_keys = self._load_api_keys()
        
        original_length = len(api_keys)
        api_keys = [k for k in api_keys if k.get("id") != key_id]
        
        if len(api_keys) < original_length:
            self._save_api_keys(api_keys)
            return True
        
        return False
    
    def record_api_key_usage(self, key_id: str):
        """Record API key usage"""
        api_keys = self._load_api_keys()
        
        for key_data in api_keys:
            if key_data.get("id") == key_id:
                key_data["last_used"] = datetime.utcnow()
                key_data["usage_count"] = key_data.get("usage_count", 0) + 1
                key_data["updated_at"] = datetime.utcnow()
                break
        
        self._save_api_keys(api_keys)


# Global instance
auth_service = AuthService()
