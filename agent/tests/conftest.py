import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brain.app import Brain, create_app
from brain.config import Settings
from brain.index import hash_embedder

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    data = tmp_path / "demo-data"
    shutil.copytree(FIXTURES, data)
    return Settings(demo_data_dir=data, chroma_dir=tmp_path / "chroma", openrouter_api_key="", anthropic_api_key="", onyx_url="", rate_limit_per_minute=1000)


@pytest.fixture
def brain(settings: Settings) -> Brain:
    return Brain(settings, embedder=hash_embedder, vectors="now")


@pytest.fixture
def client(settings: Settings, brain: Brain):
    with TestClient(create_app(settings, brain)) as client:
        yield client
