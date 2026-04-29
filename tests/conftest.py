import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from video_crawler.models.db import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def bilibili_popular_data():
    return json.loads((FIXTURES_DIR / "bilibili_popular.json").read_text())


@pytest.fixture
def bilibili_ranking_data():
    return json.loads((FIXTURES_DIR / "bilibili_ranking.json").read_text())
