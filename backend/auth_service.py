import os
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from database import User
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv()  # Fallback to default .env location

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

print(f"[AUTH_SERVICE] GOOGLE_CLIENT_ID loaded: {GOOGLE_CLIENT_ID[:20]}..." if GOOGLE_CLIENT_ID else "[AUTH_SERVICE] GOOGLE_CLIENT_ID is None!")
print(f"[AUTH_SERVICE] APP_SECRET_KEY loaded: {'Yes' if APP_SECRET_KEY else 'No'}")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), GOOGLE_CLIENT_ID
            )

            import time
            current_time = time.time()
            token_exp = idinfo.get('exp', 0)

            if token_exp < current_time:
                raise ValueError("Token has expired")

            if idinfo['aud'] != GOOGLE_CLIENT_ID:
                raise ValueError('Wrong audience.')

            user_info = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture', '')
            }
            return user_info
        except ValueError as e:
            error_msg = str(e)
            if "Token has expired" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired. Please login again."
                )
            elif "Wrong audience" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not for this application. Please login again."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token verification failed: {error_msg}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )

    def get_or_create_user(self, user_info: dict) -> User:
        """Get existing user or create new one"""
        try:
            user = self.db.query(User).filter(User.email == user_info['email']).first()

            if user:
                user.google_id = user_info['google_id']
                user.name = user_info['name']
                user.picture = user_info['picture']
                user.updated_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(user)
                return user
            else:
                user = User(
                    google_id=user_info['google_id'],
                    email=user_info['email'],
                    name=user_info['name'],
                    picture=user_info['picture']
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                return user

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token"""
        import time

        current_time = int(time.time())
        expire_time = current_time + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        to_encode = {
            "sub": str(user_id),
            "exp": expire_time,
            "iat": current_time,
            "user_id": user_id
        }

        encoded_jwt = jwt.encode(to_encode, APP_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[int]:
        """Verify JWT access token and return user ID"""
        try:
            payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except jwt.JWTError:
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id, User.is_active == True).first()

    def authenticate_user(self, google_token: str) -> tuple[User, str]:
        """Complete authentication flow"""
        user_info = self.verify_google_token(google_token)
        user = self.get_or_create_user(user_info)
        access_token = self.create_access_token(user.id)
        return user, access_token
