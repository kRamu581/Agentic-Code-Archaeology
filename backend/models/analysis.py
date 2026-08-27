from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from database import Base


class RepositoryAnalysis(Base):

    __tablename__ = "repository_analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    github_url = Column(
        String,
        nullable=False
    )

    repository_summary = Column(Text)

    intent_analysis = Column(Text)

    scope_analysis = Column(Text)

    recovery_analysis = Column(Text)

    final_report = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
