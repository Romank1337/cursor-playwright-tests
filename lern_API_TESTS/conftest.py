import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    value = os.getenv("API_BASE_URL")
    if not value:
        pytest.skip("API_BASE_URL is not set. Create .env from .env.example.")
    return value.rstrip("/")


@pytest.fixture(scope="session")
def api_session() -> requests.Session:
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_login() -> str:
    value = os.getenv("API_LOGIN")
    if not value:
        pytest.skip("API_LOGIN is not set. Create .env from .env.example.")
    return value


@pytest.fixture(scope="session")
def api_password() -> str:
    value = os.getenv("API_PASSWORD")
    if value is None:
        pytest.skip("API_PASSWORD is not set. Create .env from .env.example.")
    return value


@pytest.fixture(scope="session")
def api_basic_auth(api_login: str, api_password: str) -> tuple[str, str]:
    return api_login, api_password
