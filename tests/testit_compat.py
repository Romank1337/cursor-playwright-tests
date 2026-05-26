"""
Безопасная обёртка над пакетом testit-adapter-pytest.

Зачем это нужно:
- В CI с интеграцией Test IT мы ставим `testit-adapter-pytest`, и декораторы
  `@testit.externalId(...)`, `@testit.displayName(...)` и т.д. работают по-настоящему,
  регистрируя автотесты и отправляя результаты в TMS.
- На локальной машине разработчика, у которого нет доступа к Test IT и пакета,
  тесты должны всё равно запускаться. Поэтому если импорт `testit` падает,
  отдаём «пустой» модуль, у которого любой атрибут — это no-op декоратор.

Использование в тесте:

    from tests.testit_compat import testit

    @testit.externalId("ui.login.success_redirect")
    @testit.displayName("Успешный логин редиректит в monitoring/realtime")
    def test_success_login_redirect(...):
        ...
"""

from __future__ import annotations

from typing import Any, Callable


class _NoopTestit:
    """Заглушка модуля testit, когда пакет не установлен."""

    def __getattr__(self, _name: str) -> Callable[..., Callable[..., Any]]:
        def decorator_factory(*_args: Any, **_kwargs: Any) -> Callable[..., Any]:
            def decorator(obj: Any) -> Any:
                return obj

            return decorator

        return decorator_factory


try:
    import testit as _testit_module  # type: ignore[import-not-found]

    testit = _testit_module
    TESTIT_AVAILABLE = True
except Exception:
    testit = _NoopTestit()  # type: ignore[assignment]
    TESTIT_AVAILABLE = False


__all__ = ["testit", "TESTIT_AVAILABLE"]
