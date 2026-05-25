import os
import json
from datetime import datetime

import pytest


def _print_response_debug(test_case: str, response) -> None:
    # После каждого HTTP-запроса выводим диагностику в консоль:
    # - имя кейса (чтобы понимать, какой набор дат сейчас отработал);
    # - HTTP-статус;
    # - время ответа в секундах;
    # - превью тела ответа (обрезаем, чтобы не засорять вывод).
    # Это помогает быстро понять, что вернул API, не открывая debugger.
    body_preview = response.text[:1500]
    print(
        f"\n[{test_case}] "
        f"status={response.status_code}; "
        f"elapsed={response.elapsed.total_seconds():.3f}s\n"
        f"body: {body_preview}\n"
    )
    _append_response_log(test_case=test_case, response=response, body_preview=body_preview)


def _append_response_log(test_case: str, response, body_preview: str) -> None:
    # Пишем структурированный JSON, чтобы лог было удобно
    # читать человеком и парсить скриптами.
    try:
        body_json = response.json()
    except ValueError:
        body_json = None

    log_record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "test_case": test_case,
        "status_code": response.status_code,
        "elapsed_seconds": round(response.elapsed.total_seconds(), 3),
        "request_url": response.request.url if response.request else None,
        "response_body_preview": body_preview,
        "response_body_json": body_json,
    }

    log_line = json.dumps(log_record, ensure_ascii=False)
    with open("test_run_responses.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_line + "\n")


@pytest.fixture(scope="session")
def monitoring_value_sorted_list_path() -> str:
    # Путь к endpoint вынесен в env, потому что на разных стендах
    # один и тот же метод может иметь разный префикс маршрута.
    # Если переменная не задана, тесты сразу пропускаются понятной причиной.
    value = os.getenv("MONITORING_VALUE_SORTED_LIST_PATH")
    if not value:
        pytest.skip(
            "MONITORING_VALUE_SORTED_LIST_PATH is not set. "
            "Add it to .env for monitoring value API tests."
        )
    return value


def _build_url(api_base_url: str, monitoring_value_sorted_list_path: str) -> str:
    # Нормализуем склейку URL, чтобы не получать двойной слеш.
    # Пример: base=http://127.0.0.1:9000 и path=/MonitoringValue/... ->
    # итог: http://127.0.0.1:9000/MonitoringValue/...
    return (
        f"{api_base_url}/{monitoring_value_sorted_list_path.lstrip('/')}"
    )


def _regression_payload_for_middle_of_data() -> dict:
    # Временно не используем этот payload:
    # проверка проблемного интервала отключена по запросу.
    return _build_payload(
        from_date="2026-01-05T19:00:00.000Z",
        to_date="2026-01-06T19:01:10.001Z",
    )


def _build_payload(from_date: str, to_date: str) -> dict:
    # Отправляем полную схему запроса, чтобы избежать расхождений
    # в валидации на стороне бэкенда.
    # Здесь можно менять только даты или расширять фильтры под нужный кейс.
    return {
        "fromDate": from_date,
        "toDate": to_date,
        "pageSize": 100,
        "machineParamIntegrationIdArray": [],
        "machineParamIdArray": [],
        "machineIntegrationIdArray": [],
        "machineIdArray": [],
        "isNeedShowComment": True,
    }


@pytest.mark.parametrize(
    ("from_date", "to_date"),
    [
        ("2026-01-05T19:00:00.000Z", "2026-01-06T19:01:10.001Z"),
        ("2024-01-05T19:00:00.000Z", "2024-01-06T19:01:10.001Z"),
        ("2017-11-05T19:00:00.000Z", "2017-01-06T19:01:10.001Z"),
        ("2023-05-05T19:00:00.000Z", "2023-05-05T19:01:10.001Z"),
    ],
    ids=["early-2026-slice", "middle-2024-slice", "legacy-2017-slice", "legacy-2023-slice"],
)
def test_get_monitoring_value_sorted_list_does_not_return_500_for_time_slices(
    api_session,
    api_base_url: str,
    monitoring_value_sorted_list_path: str,
    api_basic_auth: tuple[str, str],
    from_date: str,
    to_date: str,
) -> None:
    # Основная регрессия: метод не должен падать с 500
    # на ранних, средних и поздних срезах исторических данных.
    # Этот тест параметризован, поэтому одна функция запускается
    # отдельно для КАЖДОЙ пары from_date/to_date из списка выше.
    response = api_session.post(
        _build_url(api_base_url, monitoring_value_sorted_list_path),
        json=_build_payload(from_date=from_date, to_date=to_date),
        auth=api_basic_auth,
        timeout=60,
        verify=False,
    )
    _print_response_debug(
        test_case=(
            "test_get_monitoring_value_sorted_list_does_not_return_500_for_time_slices "
            f"[{from_date}..{to_date}]"
        ),
        response=response,
    )

    # Проверка 1/2/3/4:
    # один и тот же assert выполняется 4 раза (по параметрам выше):
    # - early-2015-slice
    # - middle-2017-slice
    # - middle-2020-slice
    # - late-2025-slice
    # Логика проверки: на любом выбранном диапазоне сервер не должен
    # возвращать внутреннюю ошибку 500.
    assert response.status_code != 500, (
        "Expected non-500 response for time-slice selection. "
        f"Got 500 for [{from_date} .. {to_date}]. Response body: {response.text}"
    )
    assert response.text.strip(), (
        "Expected non-empty response body for time-slice selection. "
        f"Got empty body for [{from_date} .. {to_date}] with status {response.status_code}."
    )


def test_get_monitoring_value_sorted_list_returns_200_and_non_empty_body(
    api_session,
    api_base_url: str,
    monitoring_value_sorted_list_path: str,
    api_basic_auth: tuple[str, str],
) -> None:
    # Базовая smoke-проверка: endpoint должен вернуть 200
    # и непустое тело ответа на регрессионном диапазоне.
    response = api_session.post(
        _build_url(api_base_url, monitoring_value_sorted_list_path),
        json=_regression_payload_for_middle_of_data(),
        auth=api_basic_auth,
        timeout=60,
        verify=False,
    )
    _print_response_debug(
        test_case=(
            "test_get_monitoring_value_sorted_list_returns_200_and_non_empty_body"
        ),
        response=response,
    )

    assert response.status_code == 200, (
        "Expected 200 response for monitoring value request. "
        f"Got status: {response.status_code}. Response body: {response.text}"
    )
    assert response.text.strip(), (
        "Expected non-empty response body for status 200. "
        f"Response body: {response.text}"
    )
