from sqlalchemy.orm import Session
from database import ChatSession, ChatMessage
from datetime import datetime
import uuid
import json
from typing import List, Optional

class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, title: str = "New Chat", user_id: int = None) -> str:
        """Create a new chat session and return session_id"""
        session_id = str(uuid.uuid4())
        print(f"[CHAT_SERVICE] Creating session: {session_id}, title: {title}, user_id: {user_id}")

        try:
            db_session = ChatSession(
                session_id=session_id,
                title=title,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)

            print(f"[CHAT_SERVICE] Session created successfully: {session_id}")
            return session_id

        except Exception as e:
            print(f"[CHAT_SERVICE] Error creating session: {str(e)}")
            self.db.rollback()

            # If it's a sequence/primary key error, try to fix it
            if "duplicate key value violates unique constraint" in str(e):
                print(f"[CHAT_SERVICE] Attempting to fix sequence issue...")
                try:
                    # Fix sequence manually
                    self.db.execute("SELECT setval('chat_sessions_id_seq', COALESCE((SELECT MAX(id) FROM chat_sessions), 0) + 1, false);")
                    self.db.commit()

                    # Retry creating session
                    db_session = ChatSession(
                        session_id=session_id,
                        title=title,
                        user_id=user_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(db_session)
                    self.db.commit()
                    self.db.refresh(db_session)

                    print(f"[CHAT_SERVICE] Session created successfully after sequence fix: {session_id}")
                    return session_id

                except Exception as retry_error:
                    print(f"[CHAT_SERVICE] Failed to fix sequence and retry: {str(retry_error)}")
                    self.db.rollback()
                    raise retry_error
            else:
                raise e
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
    
    def get_all_sessions(self, user_id: int = None) -> List[ChatSession]:
        """Get all active chat sessions, optionally filtered by user"""
        print(f"[CHAT_SERVICE] Getting sessions for user_id: {user_id}")

        query = self.db.query(ChatSession).filter(ChatSession.is_active == True)

        if user_id is not None:
            query = query.filter(ChatSession.user_id == user_id)

        sessions = query.order_by(ChatSession.updated_at.desc()).all()
        print(f"[CHAT_SERVICE] Found {len(sessions)} sessions for user_id: {user_id}")

        # Debug: Print session details
        for session in sessions:
            print(f"[CHAT_SERVICE] Session: {session.session_id}, title: {session.title}, user_id: {session.user_id}")

        return sessions
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        session = self.get_session(session_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Soft delete a session"""
        session = self.get_session(session_id)
        if session:
            session.is_active = False
            session.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def add_message(self, session_id: str, message_type: str, content: str, sources: List[str] = None, summary: str = None, suggestions: str = None) -> bool:
        """Add a message to the session"""
        # Update session timestamp
        session = self.get_session(session_id)
        if not session:
            print(f"[CHAT_SERVICE] Session not found: {session_id}")
            return False

        session.updated_at = datetime.utcnow()

        # Add message - Use session.id (integer) instead of session_id (string)
        print(f"[CHAT_SERVICE] Adding message to session.id: {session.id} (session_id: {session_id})")
        db_message = ChatMessage(
            session_id=str(session.id),  # Convert integer ID to string for compatibility
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow(),
            sources=json.dumps(sources) if sources else None,
            summary=summary,
            suggestions=suggestions
        )
        self.db.add(db_message)
        self.db.commit()
        print(f"[CHAT_SERVICE] Message added successfully to session {session.id}")
        return True
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session"""
        # Get session first to get the integer ID
        session = self.get_session(session_id)
        if not session:
            print(f"[CHAT_SERVICE] Session not found for get_messages: {session_id}")
            return []

        print(f"[CHAT_SERVICE] Getting messages for session.id: {session.id} (session_id: {session_id})")
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == str(session.id)  # Use integer ID converted to string
        ).order_by(ChatMessage.timestamp.asc()).all()
    
    def generate_session_title(self, first_message: str) -> str:
        """Generate a title from the first user message"""
        # Simple title generation - take first 50 characters
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        return title if title else "New Chat"

    def deactivate_user_sessions(self, user_id: int) -> int:
        """Deactivate all sessions for a specific user and return count of deactivated sessions"""
        try:
            # Get all active sessions for the user
            active_sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).all()

            count = len(active_sessions)

            # Deactivate all sessions
            for session in active_sessions:
                session.is_active = False
                session.updated_at = datetime.utcnow()

            self.db.commit()
            print(f"[CHAT_SERVICE] Deactivated {count} sessions for user_id {user_id}")
            return count

        except Exception as e:
            print(f"[CHAT_SERVICE] Error deactivating sessions for user {user_id}: {str(e)}")
            self.db.rollback()
            return 0
