import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def settings(tmp_path):
    from app.settings import Settings
    return Settings(data_dir=str(tmp_path / "data"))


@pytest.fixture
def client(settings):
    from app.main import create_app
    with TestClient(create_app(settings)) as c:
        yield c
