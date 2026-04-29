from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from video_crawler.config import settings
from video_crawler.models.db import Base

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
