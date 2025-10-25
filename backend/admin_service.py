import os
import hashlib
from datetime import datetime, timedelta
import pytz
from typing import Optional, List, Dict
from fastapi import HTTPException, status, Request
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, String
from database import User, UserActivity, KnowledgeFile, ChatSession, ChatMessage
from dotenv import load_dotenv
import json

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv()  # Fallback to default .env location

# Admin Configuration
ADMIN_EMAIL = "admunand@gmail.com"
ADMIN_PASSWORD = "untukkedjajaanbangsa1948"
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
ALGORITHM = "HS256"
ADMIN_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

class AdminService:
    def __init__(self, db: Session):
        self.db = db
        # Set timezone to Indonesia (WIB - UTC+7)
        self.indonesia_tz = pytz.timezone('Asia/Jakarta')

    def convert_to_indonesia_time(self, utc_datetime):
        """Convert UTC datetime to Indonesia timezone"""
        if utc_datetime is None:
            return None

        # If datetime is naive (no timezone info), assume it's UTC
        if utc_datetime.tzinfo is None:
            utc_datetime = pytz.utc.localize(utc_datetime)

        # Convert to Indonesia timezone
        indonesia_time = utc_datetime.astimezone(self.indonesia_tz)
        return indonesia_time

    def authenticate_admin(self, email: str, password: str) -> bool:
        """Authenticate admin with email and password"""
        return email == ADMIN_EMAIL and password == ADMIN_PASSWORD

    def create_admin_token(self, email: str) -> str:
        """Create JWT token for admin"""
        import time
        
        current_time = int(time.time())
        expire_time = current_time + (ADMIN_TOKEN_EXPIRE_MINUTES * 60)
        
        to_encode = {
            "sub": email,
            "exp": expire_time,
            "iat": current_time,
            "type": "admin",
            "email": email
        }
        
        encoded_jwt = jwt.encode(to_encode, APP_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_admin_token(self, token: str) -> Optional[str]:
        """Verify admin JWT token and return email"""
        try:
            payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "admin":
                return None
            return email
        except jwt.JWTError:
            return None

    def log_user_activity(self, user_id: Optional[int], activity_type: str, 
                         session_id: Optional[str] = None, request: Optional[Request] = None,
                         details: Optional[Dict] = None):
        """Log user activity"""
        try:
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details) if details else None
            )
            
            self.db.add(activity)
            self.db.commit()
        except Exception as e:
            print(f"Error logging user activity: {e}")
            self.db.rollback()

    def get_user_activities(self, limit: int = 100) -> List[Dict]:
        """Get recent user activities"""
        try:
            # Rollback any failed transaction first
            self.db.rollback()

            activities = self.db.query(UserActivity)\
                .join(User, UserActivity.user_id == User.id, isouter=True)\
                .order_by(desc(UserActivity.timestamp))\
                .limit(limit)\
                .all()

            result = []
            for activity in activities:
                user_info = None
                if activity.user:
                    user_info = {
                        "id": activity.user.id,
                        "email": activity.user.email,
                        "name": activity.user.name
                    }

                # Convert timestamp to Indonesia timezone
                indonesia_time = self.convert_to_indonesia_time(activity.timestamp)

                result.append({
                    "id": activity.id,
                    "user": user_info,
                    "activity_type": activity.activity_type,
                    "session_id": activity.session_id,
                    "ip_address": activity.ip_address,
                    "timestamp": indonesia_time.isoformat(),
                    "details": json.loads(activity.details) if activity.details else None
                })

            return result
        except Exception as e:
            print(f"Error getting user activities: {e}")
            self.db.rollback()
            return []

    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        try:
            # Rollback any failed transaction first
            self.db.rollback()

            # Total users
            total_users = self.db.query(User).filter(User.is_active == True).count()

            # Active sessions (sessions with messages in last 24 hours)
            # Simplified approach: count unique session_ids from messages in last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_session_ids = self.db.query(ChatMessage.session_id)\
                .filter(ChatMessage.timestamp >= yesterday)\
                .distinct()\
                .all()

            # Convert session_ids back to integers and count matching sessions
            active_sessions = 0
            for session_id_tuple in active_session_ids:
                try:
                    session_id_int = int(session_id_tuple[0])
                    if self.db.query(ChatSession).filter(ChatSession.id == session_id_int).first():
                        active_sessions += 1
                except (ValueError, TypeError):
                    continue

            # Total chat sessions
            total_sessions = self.db.query(ChatSession).count()

            # Total messages
            total_messages = self.db.query(ChatMessage).count()

            # Users by session count
            user_session_stats = self.db.query(
                User.id,
                User.email,
                User.name,
                func.count(ChatSession.id).label('session_count')
            ).outerjoin(ChatSession, User.id == ChatSession.user_id)\
             .group_by(User.id, User.email, User.name)\
             .order_by(desc('session_count'))\
             .limit(10)\
             .all()

            user_stats = []
            for stat in user_session_stats:
                user_stats.append({
                    "user_id": stat.id,
                    "email": stat.email,
                    "name": stat.name,
                    "session_count": stat.session_count
                })

            return {
                "total_users": total_users,
                "active_sessions": active_sessions,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "top_users": user_stats
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            self.db.rollback()
            return {
                "total_users": 0,
                "active_sessions": 0,
                "total_sessions": 0,
                "total_messages": 0,
                "top_users": []
            }

    def get_knowledge_files(self) -> List[Dict]:
        """Get all knowledge base files"""
        try:
            # Rollback any failed transaction first
            self.db.rollback()

            files = self.db.query(KnowledgeFile)\
                .filter(KnowledgeFile.is_active == True)\
                .order_by(desc(KnowledgeFile.upload_date))\
                .all()

            result = []
            for file in files:
                # Convert timestamps to Indonesia timezone
                upload_date_indonesia = self.convert_to_indonesia_time(file.upload_date)
                last_processed_indonesia = self.convert_to_indonesia_time(file.last_processed) if file.last_processed else None

                result.append({
                    "id": file.id,
                    "filename": file.filename,
                    "original_filename": file.original_filename,
                    "file_size": file.file_size,
                    "file_type": file.file_type,
                    "upload_date": upload_date_indonesia.isoformat(),
                    "uploaded_by": file.uploaded_by,
                    "processed_chunks": file.processed_chunks,
                    "last_processed": last_processed_indonesia.isoformat() if last_processed_indonesia else None
                })

            return result
        except Exception as e:
            print(f"Error getting knowledge files: {e}")
            self.db.rollback()
            return []

    def get_all_users(self) -> List[Dict]:
        """Get all users with their session counts"""
        try:
            # Rollback any failed transaction first
            self.db.rollback()

            # Get all users with their session counts
            user_session_stats = self.db.query(
                User.id,
                User.email,
                User.name,
                User.created_at,
                func.count(ChatSession.id).label('session_count')
            ).outerjoin(ChatSession, User.id == ChatSession.user_id)\
             .filter(User.is_active == True)\
             .group_by(User.id, User.email, User.name, User.created_at)\
             .order_by(desc(User.created_at))\
             .all()

            result = []
            for stat in user_session_stats:
                # Convert created_at to Indonesia timezone
                indonesia_time = self.convert_to_indonesia_time(stat.created_at)

                result.append({
                    "user_id": stat.id,
                    "email": stat.email,
                    "name": stat.name,
                    "created_at": indonesia_time.isoformat(),
                    "session_count": stat.session_count
                })

            return result
        except Exception as e:
            print(f"Error getting all users: {e}")
            self.db.rollback()
            return []

    def add_knowledge_file(self, filename: str, original_filename: str, 
                          file_path: str, file_size: int, file_type: str,
                          uploaded_by: str = "admin") -> KnowledgeFile:
        """Add new knowledge file record"""
        try:
            knowledge_file = KnowledgeFile(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                uploaded_by=uploaded_by
            )
            
            self.db.add(knowledge_file)
            self.db.commit()
            self.db.refresh(knowledge_file)
            
            return knowledge_file
        except Exception as e:
            print(f"Error adding knowledge file: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add knowledge file: {str(e)}"
            )

    def update_file_processing_status(self, file_id: int, processed_chunks: int):
        """Update file processing status"""
        try:
            knowledge_file = self.db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
            if knowledge_file:
                knowledge_file.processed_chunks = processed_chunks
                knowledge_file.last_processed = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            print(f"Error updating file processing status: {e}")
            self.db.rollback()

    def delete_knowledge_file(self, file_id: int) -> bool:
        """Delete knowledge file and return file info for cleanup"""
        try:
            knowledge_file = self.db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
            if knowledge_file:
                # Store file path before deletion
                file_path = knowledge_file.file_path

                # Hard delete from database
                self.db.delete(knowledge_file)
                self.db.commit()

                # Delete physical file if it exists
                import os
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted physical file: {file_path}")

                return True
            return False
        except Exception as e:
            print(f"Error deleting knowledge file: {e}")
            self.db.rollback()
            return False
