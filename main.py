import streamlit as st
import pandas as pd
from models import generate_test_data, create_dataframes
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
    create_equipment,
    get_all_equipment,
    get_equipment_by_name,
    create_workshop,
    get_all_workshops,
    create_spare_part,
    get_all_spare_parts,
    get_spare_parts_by_equipment,
    create_replacement_record,
    get_all_replacement_records,
    get_replacement_records_by_equipment,
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
    db = SessionLocal()
    try:
        # Проверяем, есть ли данные в БД
        equipment_count = len(get_all_equipment(db))
        if equipment_count == 0:
            # Генерируем тестовые данные и сохраняем в БД
            equipment_list, workshops, spare_parts, replacement_records = (
                generate_test_data()
            )
            for eq in equipment_list:
                create_equipment(db, eq.name, eq.qty_in_fleet)
            for ws in workshops:
                create_workshop(db, ws.name, ws.address)
            for sp in spare_parts:
                eq = get_equipment_by_name(db, sp.parent_equipment)
                if eq:
                    create_spare_part(
                        db,
                        sp.name,
                        sp.useful_life_months,
                        eq.id,
                        sp.qty_per_equipment,
                        sp.qty_in_stock,
                        sp.procurement_time_days,
                    )
            for rr in replacement_records:
                eq = get_equipment_by_name(db, rr.equipment_name)
                sp = None
                for sp_obj in get_all_spare_parts(db):
                    if (
                        sp_obj.name == rr.spare_part_name
                        and sp_obj.equipment_id == eq.id
                    ):
                        sp = sp_obj
                        break
                ws = None
                for ws_obj in get_all_workshops(db):
                    if ws_obj.name == rr.workshop_name:
                        ws = ws_obj
                        break
                if eq and sp and ws:
                    create_replacement_record(
                        db,
                        eq.id,
                        sp.id,
                        ws.id,
                        rr.replacement_date,
                        rr.replacement_type,
                        rr.notes,
                    )

        # Загружаем данные из БД в DataFrames
        equipment = get_all_equipment(db)
        workshops = get_all_workshops(db)
        spare_parts = get_all_spare_parts(db)
        replacements = get_all_replacement_records(db)

        st.session_state.equipment_df = pd.DataFrame(
            [
                {
                    "id": eq.id,
                    "name": eq.name,
                    "vin": eq.vin,
                    "qty_in_fleet": eq.qty_in_fleet,
                }
                for eq in equipment
            ]
        )
        st.session_state.workshops_df = pd.DataFrame(
            [{"id": ws.id, "name": ws.name, "address": ws.address} for ws in workshops]
        )
        st.session_state.spare_parts_df = pd.DataFrame(
            [
                {
                    "id": sp.id,
                    "name": sp.name,
                    "useful_life_months": sp.useful_life_months,
                    "parent_equipment": sp.equipment.name,
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
                    "id": rr.id,
                    "equipment_name": rr.equipment.name,
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
def add_equipment(name, qty_in_fleet, vin=None):
    """
    Функция добавления Оборудования.
    name         - Название Оборудования
    qty_in_fleet - Количество в парке
    vin          - VIN номер (опционально)
    """
    db = SessionLocal()
    try:
        eq = create_equipment(db, name, qty_in_fleet, vin)
        new_row = pd.DataFrame(
            {
                "id": [eq.id],
                "name": [name],
                "vin": [vin],
                "qty_in_fleet": [qty_in_fleet],
            }
        )
        st.session_state.equipment_df = pd.concat(
            [st.session_state.equipment_df, new_row], ignore_index=True
        )
    finally:
        db.close()


def add_workshop(name, address):
    """
    Функция добавления Мастерской.
    name    - Название Мастерской
    address - Адрес Мастерской
    """
    db = SessionLocal()
    try:
        ws = create_workshop(db, name, address)
        new_row = pd.DataFrame({"id": [ws.id], "name": [name], "address": [address]})
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
        eq = get_equipment_by_name(db, parent_equipment)
        if eq:
            sp = create_spare_part(
                db,
                name,
                useful_life_months,
                eq.id,
                qty_per_equipment,
                qty_in_stock,
                procurement_time_days,
            )
            new_row = pd.DataFrame(
                {
                    "id": [sp.id],
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
    equipment_name,
    spare_part_name,
    workshop_name,
    replacement_date,
    replacement_type,
    notes,
):
    """
    Функция добавления записи о замене.
    equipment_name          - Название оборудования
    spare_part_name         - Название Запчасти
    workshop_name           - Название Мастерской
    replacement_date        - Дата замены
    replacement_type        - Тип замены - (repair-замена/scheduled-запланированная/unscheduled-незапланированная)
    notes                   - Примечания
    """
    db = SessionLocal()
    try:
        eq = get_equipment_by_name(db, equipment_name)
        sp = None
        for sp_obj in get_all_spare_parts(db):
            if sp_obj.name == spare_part_name and sp_obj.equipment_id == eq.id:
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
                    "id": [rr.id],
                    "equipment_name": [equipment_name],
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
        st.subheader("Оборудование")
        with st.expander("➕ Добавить оборудование"):
            with st.form("add_equipment_form"):
                name = st.text_input("Наименование")
                vin = st.text_input("VIN номер (опционально)")
                qty_in_fleet = st.number_input(
                    "Количество в парке", min_value=1, value=1
                )
                submitted = st.form_submit_button("Добавить")
                if submitted and name:
                    add_equipment(name, qty_in_fleet, vin if vin else None)
                    st.success("Оборудование добавлено!")
                    st.rerun()

        equipment_display_df = st.session_state.equipment_df.rename(
            columns={
                "name": "Наименование",
                "vin": "VIN",
                "qty_in_fleet": "Количество в парке",
            }
        )
        st.dataframe(equipment_display_df, width="content")

        # Выбор оборудования для просмотра замен
        selected_equipment = st.selectbox(
            "Выберите оборудование для просмотра замен:",
            st.session_state.equipment_df["name"].tolist(),
            key="equipment_replacements_select",
        )

        if selected_equipment:
            db = SessionLocal()
            try:
                eq = get_equipment_by_name(db, selected_equipment)
                if eq:
                    replacements = get_replacement_records_by_equipment(db, eq.id)
                    if replacements:
                        replacements_df = pd.DataFrame(
                            [
                                {
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
                        st.subheader(f"История замен для {selected_equipment}")
                        st.dataframe(replacements_df, width="content")
                    else:
                        st.info(
                            f"Для оборудования {selected_equipment} нет записей о заменах"
                        )
            finally:
                db.close()

    with tab2:
        st.subheader("Авторемонтные мастерские")
        with st.expander("➕ Добавить мастерскую"):
            with st.form("add_workshop_form"):
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
        st.subheader("Запчасти")
        with st.expander("➕ Добавить запчасть"):
            with st.form("add_spare_part_form"):
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
        with st.form("add_replacement_form"):
            equipment_name = st.selectbox(
                "Оборудование", st.session_state.equipment_df["name"].tolist()
            )
            # Фильтруем запчасти по выбранному оборудованию
            suitable_parts = st.session_state.spare_parts_df[
                st.session_state.spare_parts_df["parent_equipment"] == equipment_name
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
                and equipment_name
                and spare_part_name != "Нет подходящих запчастей"
            ):
                add_replacement(
                    equipment_name,
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
            "equipment_name": "Оборудование",
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

        st.subheader("Детальный анализ")

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
