import streamlit as st
import pandas as pd
from models import generate_test_data, create_dataframes
from utils import (
    calculate_wear_level,
    calculate_procurement_deadline,
    get_next_procurement_dates,
    get_wear_color,
    format_date,
    get_replacement_type_display,
    calculate_total_parts_needed,
)
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Журнал запасных частей", page_icon="🔧", layout="wide")

# Инициализация данных в session_state
if "data_initialized" not in st.session_state:
    equipment_list, workshops, spare_parts, replacement_records = generate_test_data()
    (
        st.session_state.equipment_df,
        st.session_state.workshops_df,
        st.session_state.spare_parts_df,
        st.session_state.replacements_df,
    ) = create_dataframes(equipment_list, workshops, spare_parts, replacement_records)
    st.session_state.data_initialized = True


# Функции для работы с данными
def add_equipment(name, qty_in_fleet):
    new_row = pd.DataFrame({"name": [name], "qty_in_fleet": [qty_in_fleet]})
    st.session_state.equipment_df = pd.concat(
        [st.session_state.equipment_df, new_row], ignore_index=True
    )


def add_workshop(name, address):
    new_row = pd.DataFrame({"name": [name], "address": [address]})
    st.session_state.workshops_df = pd.concat(
        [st.session_state.workshops_df, new_row], ignore_index=True
    )


def add_spare_part(
    name,
    useful_life_months,
    parent_equipment,
    qty_per_equipment,
    qty_in_stock,
    procurement_time_days,
):
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


def add_replacement(
    equipment_name,
    spare_part_name,
    workshop_name,
    replacement_date,
    replacement_type,
    notes,
):
    new_row = pd.DataFrame(
        {
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

    # Краткая статистика
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
        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(st.session_state.equipment_df, width="stretch")

        with col2:
            with st.expander("➕ Добавить оборудование"):
                with st.form("add_equipment_form"):
                    name = st.text_input("Наименование")
                    qty_in_fleet = st.number_input(
                        "Количество в парке", min_value=1, value=1
                    )
                    submitted = st.form_submit_button("Добавить")
                    if submitted and name:
                        add_equipment(name, qty_in_fleet)
                        st.success("Оборудование добавлено!")
                        st.rerun()

    with tab2:
        st.subheader("Авторемонтные мастерские")
        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(st.session_state.workshops_df, width="stretch")

        with col2:
            with st.expander("➕ Добавить мастерскую"):
                with st.form("add_workshop_form"):
                    name = st.text_input("Наименование")
                    address = st.text_input("Адрес")
                    submitted = st.form_submit_button("Добавить")
                    if submitted and name and address:
                        add_workshop(name, address)
                        st.success("Мастерская добавлена!")
                        st.rerun()

    with tab3:
        st.subheader("Запчасти")
        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(st.session_state.spare_parts_df, width="stretch")

        with col2:
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

# Учет замен
elif page == "Учет замен":
    st.title("🔄 Учет замен запчастей")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.dataframe(st.session_state.replacements_df, width="stretch")

    with col2:
        with st.expander("➕ Добавить замену"):
            with st.form("add_replacement_form"):
                equipment_name = st.selectbox(
                    "Оборудование", st.session_state.equipment_df["name"].tolist()
                )
                # Фильтруем запчасти по выбранному оборудованию
                suitable_parts = st.session_state.spare_parts_df[
                    st.session_state.spare_parts_df["parent_equipment"]
                    == equipment_name
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

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Сводка по степени износа")
            for _, row in wear_summary.iterrows():
                color = get_wear_color(row["wear_level"])
                st.markdown(
                    f"""
                <div style="background-color: {color}; padding: 10px; margin: 5px 0; border-radius: 5px; color: white;">
                    <strong>{row['wear_level'].upper()}</strong>: {row['count']} запчастей
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            # Круговая диаграмма
            fig = px.pie(
                wear_summary,
                values="count",
                names="wear_level",
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
        styled_df = wear_data.style.map(color_wear_level, subset=["wear_level"])
        st.dataframe(styled_df, width="stretch")

        # Фильтр по оборудованию
        selected_equipment = st.selectbox(
            "Фильтр по оборудованию",
            ["Все"] + wear_data["equipment_name"].unique().tolist(),
        )

        if selected_equipment != "Все":
            filtered_data = wear_data[wear_data["equipment_name"] == selected_equipment]
        else:
            filtered_data = wear_data

        st.dataframe(filtered_data, width="stretch")
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
            st.dataframe(
                procurement_needed[
                    [
                        "equipment_name",
                        "part_name",
                        "total_needed",
                        "qty_in_stock",
                        "wear_level",
                        "remaining_pct",
                        "procurement_deadline",
                    ]
                ],
                width="stretch",
            )

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
                st.dataframe(plan_df, width="stretch")

                # Визуализация плана
                fig = px.scatter(
                    plan_df,
                    x="date",
                    y="needed",
                    color="wear_level",
                    size="needed",
                    title="План закупок по датам",
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
            )
            st.plotly_chart(fig, config=dict(displayModeBar=False))
        else:
            st.info("Нет данных о заменах")

    with tab3:
        st.subheader("Анализ сроков полезного использования")
        fig = px.histogram(
            st.session_state.spare_parts_df,
            x="useful_life_months",
            title="Распределение сроков полезного использования запчастей",
        )
        st.plotly_chart(fig, config=dict(displayModeBar=False))

        fig2 = px.histogram(
            st.session_state.spare_parts_df,
            x="procurement_time_days",
            title="Распределение сроков закупки запчастей",
        )
        st.plotly_chart(fig2, config=dict(displayModeBar=False))
