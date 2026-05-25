import pytest

# Базовый URL тестируемого приложения.
# При необходимости можно вынести в переменную окружения.
BASE_URL = "https://localhost:8001"


@pytest.fixture(scope="session")
def base_url() -> str:
    # Отдаем URL как отдельную фикстуру, чтобы Page Object'ы
    # и тесты не хардкодили адрес напрямую.
    return BASE_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    # Переопределяем стандартные аргументы browser context из pytest-playwright.
    # ignore_https_errors=True нужен для локального self-signed сертификата.
    # Единый viewport делает скриншоты и поведение UI более предсказуемыми.
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {"width": 1440, "height": 900},
    }
