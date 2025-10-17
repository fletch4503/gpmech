import streamlit as st
import pandas as pd
from models import generate_test_data, create_dataframes
from init_db import initialize_database
from utils import (
    get_next_procurement_dates,
    get_wear_color,
    get_replacement_type_display,
    calculate_total_parts_needed,
)
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database import SessionLocal, create_tables, get_db
from crud import (
    create_equipment_model,
    get_equipment_model,
    get_all_equipment_models,
    get_equipment_model_by_name,
    update_equipment_model,
    delete_equipment_model,
    create_equipment,
    get_equipment_by_vin,
    get_equipment_by_model,
    update_equipment,
    delete_equipment,
    create_workshop,
    get_all_workshops,
    create_spare_part,
    get_all_spare_parts,
    get_spare_parts_by_equipment_model,
    create_replacement_record,
    get_all_replacement_records,
    get_replacement_records_by_equipment_model,
    update_replacement_record,
    delete_replacement_record,
)
from sqlalchemy.orm import Session

# Настройка страницы
st.set_page_config(page_title="Журнал запасных частей", page_icon="🔧", layout="wide")

# Инициализация базы данных
create_tables()

# Инициализация данных в session_state
if "data_initialized" not in st.session_state:
    # Инициализируем базу данных начальными данными
    initialize_database()

    db = SessionLocal()
    try:
        # Загружаем данные из БД в DataFrames
        from crud import get_all_equipment_models

        equipment_models = get_all_equipment_models(db)
        workshops = get_all_workshops(db)
        spare_parts = get_all_spare_parts(db)
        replacements = get_all_replacement_records(db)

        st.session_state.equipment_df = pd.DataFrame(
            [
                {
                    "name": model.name,
                    "qty_in_fleet": model.qty_in_fleet,
                }
                for model in equipment_models
            ]
        )
        st.session_state.workshops_df = pd.DataFrame(
            [{"name": ws.name, "address": ws.address} for ws in workshops]
        )
        st.session_state.spare_parts_df = pd.DataFrame(
            [
                {
                    "name": sp.name,
                    "useful_life_months": sp.useful_life_months,
                    "parent_equipment": sp.equipment_model.name,
                    "qty_per_equipment": sp.qty_per_equipment,
                    "qty_in_stock": sp.qty_in_stock,
                    "procurement_time_days": sp.procurement_time_days,
                }
                for sp in spare_parts
            ]
        )
        st.session_state.replacements_df = pd.DataFrame(
            [
                {
                    "equipment_vin": rr.equipment.vin,
                    "equipment_model": rr.equipment.model.name,
                    "spare_part_name": rr.spare_part.name,
                    "workshop_name": rr.workshop.name,
                    "replacement_date": rr.replacement_date,
                    "replacement_type": rr.replacement_type,
                    "notes": rr.notes,
                }
                for rr in replacements
            ]
        )
        st.session_state.data_initialized = True
    finally:
        db.close()


# Функции для работы с данными
def add_equipment_model(name, qty_in_fleet):
    """
    Функция добавления модели оборудования.
    name         - Название модели оборудования
    qty_in_fleet - Количество в парке
    """
    db = SessionLocal()
    try:
        model = create_equipment_model(db, name, qty_in_fleet)
        new_row = pd.DataFrame(
            {
                "name": [name],
                "qty_in_fleet": [qty_in_fleet],
            }
        )
        st.session_state.equipment_df = pd.concat(
            [st.session_state.equipment_df, new_row], ignore_index=True
        )
    finally:
        db.close()


def update_equipment_model_ui(model_name, new_name, new_qty_in_fleet):
    """
    Функция обновления модели оборудования.
    model_name       - Текущее название модели
    new_name         - Новое название модели
    new_qty_in_fleet - Новое количество в парке
    """
    db = SessionLocal()
    try:
        model = get_equipment_model_by_name(db, model_name)
        if model:
            updated_model = update_equipment_model(
                db, model.id, new_name, new_qty_in_fleet
            )
            if updated_model:
                # Обновляем DataFrame
                st.session_state.equipment_df.loc[
                    st.session_state.equipment_df["name"] == model_name,
                    ["name", "qty_in_fleet"],
                ] = [new_name, new_qty_in_fleet]
                return True
    finally:
        db.close()
    return False


def delete_equipment_model_ui(model_name):
    """
    Функция удаления модели оборудования.
    model_name - Название модели для удаления
    """
    db = SessionLocal()
    try:
        model = get_equipment_model_by_name(db, model_name)
        if model:
            if delete_equipment_model(db, model.id):
                # Удаляем из DataFrame
                st.session_state.equipment_df = st.session_state.equipment_df[
                    st.session_state.equipment_df["name"] != model_name
                ].reset_index(drop=True)
                return True
    finally:
        db.close()
    return False


def add_equipment_instance(model_name, vin):
    """
    Функция добавления экземпляра оборудования.
    model_name - Название модели
    vin        - VIN номер
    """
    db = SessionLocal()
    try:
        model = get_equipment_model_by_name(db, model_name)
        if model:
            equipment = create_equipment(db, model.id, vin)
            # Обновляем qty_in_fleet в модели
            update_equipment_model(db, model.id, qty_in_fleet=model.qty_in_fleet + 1)
            # Обновляем DataFrame
            st.session_state.equipment_df.loc[
                st.session_state.equipment_df["name"] == model_name, "qty_in_fleet"
            ] = (model.qty_in_fleet + 1)
            return True
    finally:
        db.close()
    return False


def update_equipment_instance(old_vin, new_vin, new_model_name):
    """
    Функция обновления экземпляра оборудования.
    old_vin       - Старый VIN
    new_vin       - Новый VIN
    new_model_name - Новое название модели
    """
    db = SessionLocal()
    try:
        equipment = get_equipment_by_vin(db, old_vin)
        if equipment:
            new_model = get_equipment_model_by_name(db, new_model_name)
            if new_model:
                updated_equipment = update_equipment(
                    db, equipment.id, new_vin, new_model.id
                )
                if updated_equipment:
                    return True
    finally:
        db.close()
    return False


def delete_equipment_instance(vin):
    """
    Функция удаления экземпляра оборудования.
    vin - VIN номер для удаления
    """
    db = SessionLocal()
    try:
        equipment = get_equipment_by_vin(db, vin)
        if equipment:
            # Получаем модель для обновления счетчика
            model = get_equipment_model(db, equipment.model_id)
            if delete_equipment(db, equipment.id) and model:
                # Обновляем qty_in_fleet
                update_equipment_model(
                    db, model.id, qty_in_fleet=model.qty_in_fleet - 1
                )
                # Обновляем DataFrame
                st.session_state.equipment_df.loc[
                    st.session_state.equipment_df["name"] == model.name, "qty_in_fleet"
                ] = (model.qty_in_fleet - 1)
                return True
    finally:
        db.close()
    return False


def add_workshop(name, address):
    """
    Функция добавления Мастерской.
    name    - Название Мастерской
    address - Адрес Мастерской
    """
    db = SessionLocal()
    try:
        ws = create_workshop(db, name, address)
        new_row = pd.DataFrame({"name": [name], "address": [address]})
        st.session_state.workshops_df = pd.concat(
            [st.session_state.workshops_df, new_row], ignore_index=True
        )
    finally:
        db.close()


def add_spare_part(
    name,
    useful_life_months,
    parent_equipment,
    qty_per_equipment,
    qty_in_stock,
    procurement_time_days,
):
    """
    Функция добавления запчасти.
    name                    - Название запчасти
    useful_life_months      - Срок службы в месяцах
    parent_equipment        - Куда устанавливается (Родительское оборудование)
    qty_per_equipment       - Количество, требуемое для установки в Родительское оборудование
    qty_in_stock            - Текущее количество на складе
    procurement_time_days   - Срок закупки запчасти (дни)
    """
    db = SessionLocal()
    try:
        eq_model = get_equipment_model_by_name(db, parent_equipment)
        if eq_model:
            sp = create_spare_part(
                db,
                name,
                useful_life_months,
                eq_model.id,
                qty_per_equipment,
                qty_in_stock,
                procurement_time_days,
            )
            new_row = pd.DataFrame(
                {
                    "name": [name],
                    "useful_life_months": [useful_life_months],
                    "parent_equipment": [parent_equipment],
                    "qty_per_equipment": [qty_per_equipment],
                    "qty_in_stock": [qty_in_stock],
                    "procurement_time_days": [procurement_time_days],
                }
            )
            st.session_state.spare_parts_df = pd.concat(
                [st.session_state.spare_parts_df, new_row], ignore_index=True
            )
    finally:
        db.close()


def add_replacement(
    equipment_vin,
    spare_part_name,
    workshop_name,
    replacement_date,
    replacement_type,
    notes,
):
    """
    Функция добавления записи о замене.
    equipment_vin           - VIN номер оборудования
    spare_part_name         - Название Запчасти
    workshop_name           - Название Мастерской
    replacement_date        - Дата замены
    replacement_type        - Тип замены - (repair-замена/scheduled-запланированная/unscheduled-незапланированная)
    notes                   - Примечания
    """
    db = SessionLocal()
    try:
        eq = get_equipment_by_vin(db, equipment_vin)
        sp = None
        for sp_obj in get_all_spare_parts(db):
            if (
                sp_obj.name == spare_part_name
                and sp_obj.equipment_model_id == eq.model_id
            ):
                sp = sp_obj
                break
        ws = None
        for ws_obj in get_all_workshops(db):
            if ws_obj.name == workshop_name:
                ws = ws_obj
                break
        if eq and sp and ws:
            rr = create_replacement_record(
                db, eq.id, sp.id, ws.id, replacement_date, replacement_type, notes
            )
            new_row = pd.DataFrame(
                {
                    "equipment_vin": [equipment_vin],
                    "equipment_model": [eq.model.name],
                    "spare_part_name": [spare_part_name],
                    "workshop_name": [workshop_name],
                    "replacement_date": [replacement_date],
                    "replacement_type": [replacement_type],
                    "notes": [notes],
                }
            )
            st.session_state.replacements_df = pd.concat(
                [st.session_state.replacements_df, new_row], ignore_index=True
            )
    finally:
        db.close()


# Навигация
st.sidebar.title("Навигация")
page = st.sidebar.radio(
    "Выберите раздел:",
    [
        "Главная",
        "Справочники",
        "Учет замен",
        "Анализ износа",
        "План закупок",
        "Визуализации",
    ],
)

# Главная страница
if page == "Главная":
    st.title("🔧 Журнал запасных частей")
    st.markdown(
        """
    Добро пожаловать в систему учета запасных частей!

    **Функционал системы:**
    - 📋 Управление справочниками (оборудование, запчасти, мастерские)
    - 🔄 Учет замен запчастей
    - 📊 Анализ степени износа с цветовой индикацией
    - 📅 Формирование плана закупок
    - 📈 Визуализация данных

    Выберите раздел в боковой панели для начала работы.
    """
    )

    # Краткая статистика в Footer-е
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Оборудование", len(st.session_state.equipment_df))
    with col2:
        st.metric("Запчасти", len(st.session_state.spare_parts_df))
    with col3:
        st.metric("Мастерские", len(st.session_state.workshops_df))
    with col4:
        st.metric("Замен", len(st.session_state.replacements_df))

# Справочники
elif page == "Справочники":
    st.title("📋 Справочники")

    tab1, tab2, tab3 = st.tabs(["Оборудование", "Мастерские", "Запчасти"])

    with tab1:
        st.subheader(":blue[Оборудование]", divider="blue")
        # st.subheader("Оборудование", divider="blue")

        # Создаем две колонки
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Список моделей оборудования", divider="grey")

            # Управление моделями оборудования
            equipment_display_df = st.session_state.equipment_df.rename(
                columns={
                    "name": "Наименование модели",
                    "qty_in_fleet": "Количество в парке",
                }
            )

            # Выбор модели для редактирования/удаления
            if not equipment_display_df.empty:
                selected_model_for_edit = st.selectbox(
                    "Выберите модель для редактирования/удаления:",
                    equipment_display_df["Наименование модели"].tolist(),
                    key="model_edit_select",
                )

                col_edit, col_delete = st.columns(2)

                with col_edit:
                    if st.button("✏️ Редактировать", key="edit_model_btn"):
                        st.session_state.edit_model_mode = True
                        st.session_state.selected_model = selected_model_for_edit

                with col_delete:
                    if st.button("🗑️ Удалить", key="delete_model_btn"):
                        if delete_equipment_model_ui(selected_model_for_edit):
                            st.success(f"Модель '{selected_model_for_edit}' удалена!")
                            st.rerun()
                        else:
                            st.error("Ошибка при удалении модели")

                # Форма редактирования модели
                if (
                    st.session_state.get("edit_model_mode", False)
                    and st.session_state.get("selected_model")
                    == selected_model_for_edit
                ):
                    current_data = st.session_state.equipment_df[
                        st.session_state.equipment_df["name"] == selected_model_for_edit
                    ].iloc[0]

                    with st.form("edit_equipment_form", width="content"):
                        st.subheader(
                            f"Редактирование модели: {selected_model_for_edit}"
                        )
                        new_name = st.text_input(
                            "Наименование модели", value=current_data["name"]
                        )
                        new_qty = st.number_input(
                            "Количество в парке",
                            min_value=0,
                            value=int(current_data["qty_in_fleet"]),
                        )
                        submitted_edit = st.form_submit_button("Сохранить изменения")
                        cancel_edit = st.form_submit_button("Отмена")

                        if submitted_edit and new_name:
                            if update_equipment_model_ui(
                                selected_model_for_edit, new_name, new_qty
                            ):
                                st.success("Модель обновлена!")
                                st.session_state.edit_model_mode = False
                                st.rerun()
                            else:
                                st.error("Ошибка при обновлении модели")
                        elif cancel_edit:
                            st.session_state.edit_model_mode = False
                            st.rerun()

                with st.expander("➕ Добавить модель оборудования", width="stretch"):
                    with st.form("add_equipment_form", width="content"):
                        name = st.text_input("Наименование модели")
                        qty_in_fleet = st.number_input(
                            "Количество в парке", min_value=1, value=1
                        )
                        submitted = st.form_submit_button("Добавить")
                        if submitted and name:
                            add_equipment_model(name, qty_in_fleet)
                            st.success("Модель оборудования добавлена!")
                            st.rerun()

            st.dataframe(equipment_display_df, width="content")

        with col2:
            st.subheader("Просмотр и редактирование модели", divider="gray")
            # Выбор модели оборудования для просмотра VIN
            selected_equipment_model = st.selectbox(
                "Выберите модель оборудования для просмотра/добавления/редактирования VIN:",
                st.session_state.equipment_df["name"].tolist(),
                key="equipment_vin_select",
            )

            if selected_equipment_model:
                db = SessionLocal()
                try:
                    eq_model = get_equipment_model_by_name(db, selected_equipment_model)
                    if eq_model:
                        equipment_instances = get_equipment_by_model(db, eq_model.id)
                        if equipment_instances:
                            vin_df = pd.DataFrame(
                                [{"VIN": eq.vin} for eq in equipment_instances]
                            )

                            # Управление экземплярами оборудования
                            # Выбор VIN для редактирования/удаления
                            if not vin_df.empty:
                                selected_vin_for_edit = st.selectbox(
                                    "Выберите VIN для редактирования/удаления:",
                                    vin_df["VIN"].tolist(),
                                    key="vin_edit_select",
                                )

                                col_edit_vin, col_delete_vin = st.columns(
                                    2, border=True
                                )

                                with col_edit_vin:
                                    if st.button(
                                        "✏️ Редактировать VIN", key="edit_vin_btn"
                                    ):
                                        st.session_state.edit_vin_mode = True
                                        st.session_state.selected_vin = (
                                            selected_vin_for_edit
                                        )

                                with col_delete_vin:
                                    if st.button("🗑️ Удалить VIN", key="delete_vin_btn"):
                                        if delete_equipment_instance(
                                            selected_vin_for_edit
                                        ):
                                            st.success(
                                                f"VIN '{selected_vin_for_edit}' удален!"
                                            )
                                            st.rerun()
                                        else:
                                            st.error("Ошибка при удалении VIN")

                                # Форма редактирования VIN
                                if (
                                    st.session_state.get("edit_vin_mode", False)
                                    and st.session_state.get("selected_vin")
                                    == selected_vin_for_edit
                                ):
                                    with st.form("edit_vin_form", width="content"):
                                        st.subheader(
                                            f"Редактирование VIN: {selected_vin_for_edit}"
                                        )
                                        new_vin = st.text_input(
                                            "Новый VIN номер",
                                            value=selected_vin_for_edit,
                                        )
                                        new_model = st.selectbox(
                                            "Модель оборудования",
                                            st.session_state.equipment_df[
                                                "name"
                                            ].tolist(),
                                            index=st.session_state.equipment_df["name"]
                                            .tolist()
                                            .index(selected_equipment_model),
                                        )
                                        submitted_edit_vin = st.form_submit_button(
                                            "Сохранить изменения"
                                        )
                                        cancel_edit_vin = st.form_submit_button(
                                            "Отмена"
                                        )

                                        if submitted_edit_vin and new_vin:
                                            if update_equipment_instance(
                                                selected_vin_for_edit,
                                                new_vin,
                                                new_model,
                                            ):
                                                st.success("VIN обновлен!")
                                                st.session_state.edit_vin_mode = False
                                                st.rerun()
                                            else:
                                                st.error("Ошибка при обновлении VIN")
                                        elif cancel_edit_vin:
                                            st.session_state.edit_vin_mode = False
                                            st.rerun()

                            with st.expander(
                                "➕ Добавить VIN оборудования", width="stretch"
                            ):
                                with st.form(
                                    "add_equipment_instance_form", width="content"
                                ):
                                    vin_input = st.text_input("VIN номер")
                                    submitted_add = st.form_submit_button("Добавить")
                                    if submitted_add and vin_input:
                                        if add_equipment_instance(
                                            selected_equipment_model, vin_input
                                        ):
                                            st.success(
                                                "Экземпляр оборудования добавлен!"
                                            )
                                            st.rerun()
                                        else:
                                            st.error("Ошибка при добавлении экземпляра")

                            # st.subheader("VIN-номера", divider="gray")
                            st.dataframe(vin_df, width="content")
                        else:
                            st.info("Нет экземпляров оборудования для этой модели")
                    else:
                        st.info("Модель не найдена")
                finally:
                    db.close()
            else:
                st.info("Выберите модель оборудования для просмотра VIN")

        st.subheader(
            "История замен -> Выберите оборудование для просмотра", divider="gray"
        )
        # Выбор модели оборудования для просмотра замен (ниже колонок)
        selected_equipment_model_replacements = st.selectbox(
            "Выберите модель оборудования для просмотра замен:",
            st.session_state.equipment_df["name"].tolist(),
            key="equipment_replacements_select",
        )

        if selected_equipment_model_replacements:
            db = SessionLocal()
            try:
                eq_model = get_equipment_model_by_name(
                    db, selected_equipment_model_replacements
                )
                if eq_model:
                    replacements = get_replacement_records_by_equipment_model(
                        db, eq_model.id
                    )
                    if replacements:
                        replacements_df = pd.DataFrame(
                            [
                                {
                                    "VIN": rr.equipment.vin,
                                    "Дата замены": rr.replacement_date.strftime(
                                        "%d.%m.%Y"
                                    ),
                                    "Запчасть": rr.spare_part.name,
                                    "Мастерская": rr.workshop.name,
                                    "Тип замены": get_replacement_type_display(
                                        rr.replacement_type
                                    ),
                                    "Примечания": rr.notes or "",
                                }
                                for rr in replacements
                            ]
                        ).sort_values("Дата замены", ascending=False)
                        st.subheader(
                            f"История замен для модели {selected_equipment_model_replacements}"
                        )
                        st.dataframe(replacements_df, width="content")
                    else:
                        st.info(
                            f"Для модели оборудования {selected_equipment_model_replacements} нет записей о заменах"
                        )
            finally:
                db.close()

    with tab2:
        st.subheader(":blue[Авторемонтные мастерские]", divider="blue")
        with st.expander("➕ Добавить мастерскую"):
            with st.form("add_workshop_form", width="content"):
                name = st.text_input("Наименование")
                address = st.text_input("Адрес")
                submitted = st.form_submit_button("Добавить")
                if submitted and name and address:
                    add_workshop(name, address)
                    st.success("Мастерская добавлена!")
                    st.rerun()

        workshops_display_df = st.session_state.workshops_df.rename(
            columns={
                "name": "Наименование",
                "address": "Адрес",
            }
        )
        st.dataframe(workshops_display_df, width="content")

    with tab3:
        st.subheader(":blue[Запчасти]", divider="blue")
        with st.expander("➕ Добавить запчасть"):
            with st.form("add_spare_part_form", width="content"):
                name = st.text_input("Наименование")
                useful_life_months = st.number_input(
                    "Срок полезного использования (месяцы)", min_value=1, value=12
                )
                parent_equipment = st.selectbox(
                    "Родительское оборудование",
                    st.session_state.equipment_df["name"].tolist(),
                )
                qty_per_equipment = st.number_input(
                    "Количество в единице оборудования", min_value=1, value=1
                )
                qty_in_stock = st.number_input(
                    "Количество на складе", min_value=0, value=0
                )
                procurement_time_days = st.number_input(
                    "Срок закупки (дни)", min_value=1, value=7
                )
                submitted = st.form_submit_button("Добавить")
                if submitted and name:
                    add_spare_part(
                        name,
                        useful_life_months,
                        parent_equipment,
                        qty_per_equipment,
                        qty_in_stock,
                        procurement_time_days,
                    )
                    st.success("Запчасть добавлена!")
                    st.rerun()

        spare_parts_display_df = st.session_state.spare_parts_df.rename(
            columns={
                "name": "Наименование",
                "useful_life_months": "Срок службы (месяцы)",
                "parent_equipment": "Оборудование",
                "qty_per_equipment": "Кол-во на единицу",
                "qty_in_stock": "На складе",
                "procurement_time_days": "Срок закупки (дни)",
            }
        )
        st.dataframe(spare_parts_display_df, width="content")

# Учет замен
elif page == "Учет замен":
    st.title("🔄 Учет замен запчастей")

    # Форма добавления замены сразу после заголовка
    with st.expander("➕ Добавить замену"):
        with st.form("add_replacement_form", width="content"):
            # Выбор модели оборудования
            equipment_model_name = st.selectbox(
                "Модель оборудования", st.session_state.equipment_df["name"].tolist()
            )

            # Получаем список VIN для выбранной модели
            db = SessionLocal()
            vin_options = []
            try:
                eq_model = get_equipment_model_by_name(db, equipment_model_name)
                if eq_model:
                    equipment_instances = get_equipment_by_model(db, eq_model.id)
                    vin_options = [eq.vin for eq in equipment_instances]
            finally:
                db.close()

            if vin_options:
                equipment_vin = st.selectbox("VIN номер оборудования", vin_options)
            else:
                st.error("Для выбранной модели нет экземпляров оборудования")
                equipment_vin = None

            # Фильтруем запчасти по выбранной модели оборудования
            suitable_parts = st.session_state.spare_parts_df[
                st.session_state.spare_parts_df["parent_equipment"]
                == equipment_model_name
            ]["name"].tolist()
            spare_part_name = st.selectbox(
                "Запчасть",
                suitable_parts if suitable_parts else ["Нет подходящих запчастей"],
            )
            workshop_name = st.selectbox(
                "Мастерская", st.session_state.workshops_df["name"].tolist()
            )
            replacement_date = st.date_input("Дата замены", datetime.now().date())
            replacement_type = st.selectbox(
                "Тип замены",
                ["repair", "scheduled", "unscheduled"],
                format_func=get_replacement_type_display,
            )
            notes = st.text_area("Примечания", height=100)
            submitted = st.form_submit_button("Добавить")
            if (
                submitted
                and equipment_vin
                and spare_part_name != "Нет подходящих запчастей"
            ):
                add_replacement(
                    equipment_vin,
                    spare_part_name,
                    workshop_name,
                    pd.to_datetime(replacement_date),
                    replacement_type,
                    notes,
                )
                st.success("Замена добавлена!")
                st.rerun()

    # Таблица замен
    replacements_display_df = st.session_state.replacements_df.rename(
        columns={
            "equipment_vin": "VIN оборудования",
            "equipment_model": "Модель оборудования",
            "spare_part_name": "Запчасть",
            "workshop_name": "Мастерская",
            "replacement_date": "Дата замены",
            "replacement_type": "Тип замены",
            "notes": "Примечания",
        }
    )
    st.dataframe(replacements_display_df, width="content")

# Анализ износа
elif page == "Анализ износа":
    st.title("📊 Анализ степени износа")

    # Расчет данных об износе
    wear_data = calculate_total_parts_needed(
        st.session_state.equipment_df,
        st.session_state.spare_parts_df,
        st.session_state.replacements_df,
    )

    if not wear_data.empty:
        # Группировка по степени износа
        wear_summary = wear_data.groupby("wear_level").size().reset_index(name="count")
        st.subheader("Сводка по степени износа")
        for _, row in wear_summary.iterrows():
            color = get_wear_color(row["wear_level"])
            if row["wear_level"] == "green":
                description = "осталось более 25% от срока полезной эксплуатации"
            elif row["wear_level"] == "yellow":
                description = "осталось менее 25% от срока полезной эксплуатации"
            elif row["wear_level"] == "red":
                description = "осталось менее 10% от срока полезной эксплуатации"
            else:
                description = ""
            st.markdown(
                f"""
            <div style="background-color: {color}; padding: 10px; margin: 5px 0; border-radius: 5px; color: white; display: inline-block; width: auto;">
                <strong>{row['wear_level'].upper()}</strong>: {row['count']} запчастей ({description})
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Круговая диаграмма
        fig = px.pie(
            wear_summary,
            values="count",
            names="wear_level",
            labels={"wear_level": "Уровень износа"},
            title="Распределение по степени износа",
            color="wear_level",
            color_discrete_map={
                "green": "#28a745",
                "yellow": "#ffc107",
                "red": "#dc3545",
            },
        )
        st.plotly_chart(fig, config=dict(displayModeBar=False))

        st.subheader("Детальный анализ", divider="grey")

        # Добавляем цветовую индикацию
        def color_wear_level(val):
            color = get_wear_color(val)
            return f"background-color: {color}; color: white"

        # styled_df = wear_data.style.applymap(color_wear_level, subset=["wear_level"])
        wear_display_df = wear_data.rename(
            columns={
                "equipment_name": "Оборудование",
                "part_name": "Запчасть",
                "total_needed": "Требуется",
                "qty_in_stock": "На складе",
                "wear_level": "Степень износа",
                "remaining_pct": "Остаток (%)",
                "procurement_deadline": "Срок закупки",
                "procurement_time_days": "Время на закупку, дн.",
            }
        )
        styled_df = wear_display_df.style.map(
            color_wear_level, subset=["Степень износа"]
        )
        st.dataframe(styled_df, width="content")

        # Фильтр по оборудованию
        selected_equipment = st.selectbox(
            "Фильтр по оборудованию",
            ["Все"] + wear_data["equipment_name"].unique().tolist(),
        )

        if selected_equipment != "Все":
            filtered_data = wear_data[wear_data["equipment_name"] == selected_equipment]
        else:
            filtered_data = wear_data

        filtered_display_df = filtered_data.rename(
            columns={
                "equipment_name": "Оборудование",
                "part_name": "Запчасть",
                "total_needed": "Требуется",
                "qty_in_stock": "На складе",
                "wear_level": "Степень износа",
                "remaining_pct": "Остаток (%)",
                "procurement_deadline": "Срок закупки",
                "procurement_time_days": "Время на закупку, дн.",
            }
        )
        st.dataframe(filtered_display_df, width="content")
    else:
        st.info("Нет данных для анализа износа")

# План закупок
elif page == "План закупок":
    st.title("📅 План закупки запчастей")

    # Расчет плана закупок
    procurement_data = calculate_total_parts_needed(
        st.session_state.equipment_df,
        st.session_state.spare_parts_df,
        st.session_state.replacements_df,
    )

    if not procurement_data.empty:
        # Фильтруем только те запчасти, которые требуют закупки
        procurement_needed = procurement_data[
            (procurement_data["wear_level"].isin(["yellow", "red"]))
            | (procurement_data["qty_in_stock"] < procurement_data["total_needed"])
        ].copy()

        if not procurement_needed.empty:
            # Расчет дат закупки
            procurement_needed["next_procurement_dates"] = procurement_needed[
                "procurement_deadline"
            ].apply(lambda x: get_next_procurement_dates(x) if pd.notna(x) else [])

            st.subheader("Запчасти, требующие закупки")
            procurement_display_df = procurement_needed[
                [
                    "equipment_name",
                    "part_name",
                    "total_needed",
                    "qty_in_stock",
                    "wear_level",
                    "remaining_pct",
                    "procurement_deadline",
                ]
            ].rename(
                columns={
                    "equipment_name": "Оборудование",
                    "part_name": "Запчасть",
                    "total_needed": "Требуется",
                    "qty_in_stock": "На складе",
                    "wear_level": "Степень износа",
                    "remaining_pct": "Остаток (%)",
                    "procurement_deadline": "Срок закупки",
                }
            )
            st.dataframe(procurement_display_df, width="content")

            # Группировка по датам
            procurement_plan = []
            for _, row in procurement_needed.iterrows():
                if row["next_procurement_dates"]:
                    for proc_date in row["next_procurement_dates"]:
                        procurement_plan.append(
                            {
                                "date": proc_date,
                                "equipment": row["equipment_name"],
                                "part": row["part_name"],
                                "needed": row["total_needed"] - row["qty_in_stock"],
                                "wear_level": row["wear_level"],
                            }
                        )

            if procurement_plan:
                plan_df = pd.DataFrame(procurement_plan).sort_values("date")
                st.subheader("Календарный план закупок")
                plan_display_df = plan_df.rename(
                    columns={
                        "date": "Дата",
                        "equipment": "Оборудование",
                        "part": "Запчасть",
                        "needed": "Требуется",
                        "wear_level": "Срочность",
                    }
                )
                st.dataframe(plan_display_df, width="content")

                # Визуализация плана
                # Убедимся, что значения 'needed' положительные для корректного отображения
                plan_df["needed"] = plan_df["needed"].clip(
                    lower=1
                )  # Минимум 1 для отображения
                fig = px.scatter(
                    plan_df,
                    x="date",
                    y="needed",
                    color="wear_level",
                    size="needed",
                    title="План закупок по датам",
                    labels={
                        "date": "Дата закупки",
                        "needed": "Необходимо, шт.",
                    },
                    color_discrete_map={
                        "green": "#28a745",
                        "yellow": "#ffc107",
                        "red": "#dc3545",
                    },
                )
                st.plotly_chart(fig, config=dict(displayModeBar=False))
            else:
                st.info("Нет запчастей, требующих срочной закупки")
        else:
            st.success("Все запчасти в достаточном количестве!")
    else:
        st.info("Нет данных для формирования плана закупок")

# Визуализации
elif page == "Визуализации":
    st.title("📈 Визуализации")

    tab1, tab2, tab3 = st.tabs(
        ["Распределение запчастей", "История замен", "Анализ сроков"]
    )

    with tab1:
        st.subheader("Распределение запчастей по оборудованию")
        parts_by_equipment = (
            st.session_state.spare_parts_df.groupby("parent_equipment")
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            parts_by_equipment,
            x="parent_equipment",
            y="count",
            title="Количество запчастей по типам оборудования",
            labels={
                "parent_equipment": "Тип Оборудования",
                "count": "Количество",
            },
        )
        st.plotly_chart(fig, config=dict(displayModeBar=False))

    with tab2:
        st.subheader("История замен по времени")
        if not st.session_state.replacements_df.empty:
            replacements_over_time = st.session_state.replacements_df.copy()
            replacements_over_time["month"] = replacements_over_time[
                "replacement_date"
            ].dt.to_period("M")
            monthly_replacements = (
                replacements_over_time.groupby("month").size().reset_index(name="count")
            )
            monthly_replacements["month"] = monthly_replacements["month"].astype(str)

            fig = px.line(
                monthly_replacements,
                x="month",
                y="count",
                title="Количество замен по месяцам",
                labels={
                    "month": "Месяц",
                    "count": "Количество",
                },
            )
            st.plotly_chart(fig, config=dict(displayModeBar=False))
        else:
            st.info("Нет данных о заменах")

    with tab3:
        st.subheader("Анализ сроков полезного использования")
        fig = px.histogram(
            st.session_state.spare_parts_df,
            x="useful_life_months",
            # y="count",
            title="Распределение сроков полезного использования запчастей",
            labels={
                "count": "Количество запчастей",
                "useful_life_months": "Срок службы (месяцы)",
            },
        )
        st.plotly_chart(fig, config=dict(displayModeBar=False))

        fig2 = px.histogram(
            st.session_state.spare_parts_df,
            x="procurement_time_days",
            # y="count",
            title="Распределение сроков закупки запчастей",
            labels={
                "count": "Количество запчастей",
                "procurement_time_days": "Срок закупки (Дни)",
            },
        )
        st.plotly_chart(fig2, config=dict(displayModeBar=False))
