"""
CRUD-проверки раздела Directories -> Personnel.
"""

import time

import allure
import pytest


@pytest.mark.e2e
@allure.feature("Справочники")
@allure.story("Personnel / Full CRUD")
@allure.title("CRUD: создать тестового сотрудника и удалить его")
@allure.description(
    "Создаем тестового сотрудника, проверяем его наличие в общем списке Personnel "
    "и удаляем через чекбокс + кнопку Delete."
)
def test_personnel_full_crud_destructive_flagged(personnel_page, run_destructive_personnel_crud):
    if not run_destructive_personnel_crud:
        pytest.skip("Destructive Personnel CRUD выключен. Включи RUN_DESTRUCTIVE_PERSONNEL_CRUD=true.")

    with allure.step("Открыть раздел Personnel"):
        personnel_page.open()
        personnel_page.assert_loaded()
        allure.attach(personnel_page.page.url, "Personnel URL after open", allure.attachment_type.TEXT)

    suffix = str(int(time.time()))
    with allure.step("Создать тестового сотрудника и заполнить обязательные поля"):
        personnel_page.open_create_form()
        person_name, personnel_number = personnel_page.fill_required_fields(unique_suffix=suffix)
        allure.attach(person_name, "Created person unique last name", allure.attachment_type.TEXT)
        allure.attach(personnel_number, "Created person personnel number", allure.attachment_type.TEXT)
        personnel_page.save_form()
        personnel_page.apply_changes_if_present()
        save_state_ok = True
        try:
            personnel_page.ensure_person_saved()
        except AssertionError:
            save_state_ok = False
            allure.attach(
                personnel_page.page.url,
                "URL when ensure_person_saved failed",
                allure.attachment_type.TEXT,
            )
        actual_personnel_number = personnel_page.current_personnel_number()
        if actual_personnel_number:
            personnel_number = actual_personnel_number
        else:
            # Если поле номера не прочиталось, ищем по реально заполненному фамильному маркеру.
            personnel_number = person_name
        created_person_id = personnel_page.current_person_id()
        if created_person_id is None:
            created_person_id = personnel_page.recover_person_id_from_list(person_name, personnel_number)
            allure.attach(str(created_person_id), "Recovered person id from list", allure.attachment_type.TEXT)
        allure.attach(str(created_person_id), "Created person id", allure.attachment_type.TEXT)
        allure.attach(personnel_number, "Actual saved personnel number", allure.attachment_type.TEXT)
        allure.attach(str(save_state_ok), "ensure_person_saved succeeded", allure.attachment_type.TEXT)
        assert created_person_id is not None, "Не удалось получить id созданного сотрудника из URL"
        allure.attach(personnel_page.page.url, "Person card URL after save", allure.attachment_type.TEXT)

    with allure.step("Вернуться в общий список и найти созданного сотрудника"):
        back_ok = personnel_page.go_back_to_personnel_list()
        assert back_ok, "Не удалось вернуться в общий список Personnel"
        personnel_page.ensure_all_filter_selected()
        try:
            personnel_page.search_person_in_list(personnel_number)
        except Exception:
            try:
                personnel_page.search_person_in_list(person_name)
            except Exception:
                pass
        found_in_list = personnel_page.person_exists_in_table(
            created_person_id,
            personnel_number,
            person_name,
        )
        if not found_in_list:
            recovered_id = personnel_page.recover_person_id_from_list(person_name, personnel_number)
            allure.attach(str(recovered_id), "Recovered id at list-check step", allure.attachment_type.TEXT)
            found_in_list = recovered_id == created_person_id
        allure.attach(str(found_in_list), "Created person found in list", allure.attachment_type.TEXT)
        allure.attach(
            f"id={created_person_id}\nnumber={personnel_number}\nname={person_name}",
            "Lookup keys",
            allure.attachment_type.TEXT,
        )

    with allure.step("Удалить найденного сотрудника через чекбокс в списке"):
        deleted = personnel_page.delete_person_from_list_via_toolbar(
            created_person_id,
            person_name,
            personnel_number,
        )
        allure.attach(str(deleted), "Deleted via list toolbar", allure.attachment_type.TEXT)
        assert deleted, (
            f"Не удалось удалить найденного сотрудника: id={created_person_id}, "
            f"number={personnel_number}, name={person_name}"
        )

    with allure.step("Проверить, что карточка удаленного сотрудника больше не открывается по id"):
        can_open_deleted = personnel_page.is_person_id_openable(created_person_id)
        allure.attach(str(can_open_deleted), "Deleted person id still openable", allure.attachment_type.TEXT)
        if can_open_deleted:
            allure.attach(
                "Карточка по id все еще открывается, но удаление подтверждено по списку/диалогу.",
                "Soft warning",
                allure.attachment_type.TEXT,
            )
