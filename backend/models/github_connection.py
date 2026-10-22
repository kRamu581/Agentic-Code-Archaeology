from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from database import Base


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    session_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    encrypted_token = Column(Text, nullable=False)
    scopes = Column(String, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
