import pandas as pd
from datetime import datetime, timedelta
from logly import logger
from functools import wraps

cust_color = {"INFO": "GREEN", "ERROR": "BRIGHT_RED"}

logger.configure(
    level="INFO",
    json=False,
    color=True,
    level_colors=cust_color,
    auto_sink=True,
)


def funcenter(func):  # Измеряем время на работу функций
    @wraps(func)
    def wrapper(*a, **kw):
        result = func(*a, **kw)
        logger.info(f"Вошли в метод {func.__name__}")
        return result

    return wrapper


# @funcenter
def calculate_wear_level(replacement_date, useful_life_months):
    """
    Расчет степени износа запчасти
    Возвращает: 'green', 'yellow', 'red' и процент оставшегося срока
    """
    if pd.isna(replacement_date):
        return "red", 0  # Если нет даты замены, считаем полностью изношенной

    current_date = datetime.now()
    months_passed = (
        current_date - replacement_date
    ).days / 30.44  # Среднее количество дней в месяце
    remaining_months = useful_life_months - months_passed
    remaining_percentage = (remaining_months / useful_life_months) * 100

    if remaining_percentage > 25:
        return "green", max(0, remaining_percentage)
    elif remaining_percentage > 10:
        return "yellow", max(0, remaining_percentage)
    else:
        return "red", max(0, remaining_percentage)


# @funcenter
def calculate_procurement_deadline(
    replacement_date, useful_life_months, procurement_time_days
):
    """
    Расчет самой поздней даты инициации закупки
    """
    if pd.isna(replacement_date):
        return None

    # Дата окончания полезного использования
    end_of_life = replacement_date + timedelta(days=useful_life_months * 30.44)

    # Вычитаем срок закупки
    procurement_deadline = end_of_life - timedelta(days=procurement_time_days)

    return procurement_deadline


def get_next_procurement_dates(initiation_date):
    """
    Получение возможных дат закупки: 10-е и 25-е числа следующего месяца после даты инициации
    """
    if pd.isna(initiation_date):
        return []

    # Следующий месяц после даты инициации
    next_month = initiation_date.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)

    date_10 = next_month.replace(day=10)
    date_25 = next_month.replace(day=25)

    return [date_10, date_25]


def get_wear_color(wear_level):
    """Получение цвета для отображения степени износа"""
    colors = {"green": "#28a745", "yellow": "#ffc107", "red": "#dc3545"}
    return colors.get(wear_level, "#6c757d")


# @funcenter
def format_date(date):
    """Форматирование даты для отображения"""
    if pd.isna(date):
        return "Не указано"
    return date.strftime("%d.%m.%Y")


# @funcenter
def get_replacement_type_display(replacement_type):
    """Получение читаемого названия типа замены."""
    types = {
        "repair": "Ремонт",
        "scheduled": "Плановая замена",
        "unscheduled": "Внеплановая замена",
    }
    return types.get(replacement_type, replacement_type)


# @funcenter
def calculate_total_parts_needed(equipment_df, spare_parts_df, replacements_df):
    """
    Расчет общего количества необходимых запчастей для всего парка.
    """
    result = []

    for _, equipment in equipment_df.iterrows():
        equipment_name = equipment["name"]
        qty_in_fleet = equipment["qty_in_fleet"]

        # Запчасти для этого оборудования
        equipment_parts = spare_parts_df[
            spare_parts_df["parent_equipment"] == equipment_name
        ]

        for _, part in equipment_parts.iterrows():
            part_name = part["name"]
            qty_per_equipment = part["qty_per_equipment"]
            qty_in_stock = part["qty_in_stock"]
            useful_life_months = part["useful_life_months"]
            procurement_time_days = part["procurement_time_days"]

            # Общее количество необходимых запчастей
            total_needed = qty_in_fleet * qty_per_equipment

            # Последние замены для этой запчасти в этом оборудовании
            part_replacements = replacements_df[
                (replacements_df["equipment_name"] == equipment_name)
                & (replacements_df["spare_part_name"] == part_name)
            ].sort_values("replacement_date", ascending=False)

            if not part_replacements.empty:
                last_replacement = part_replacements.iloc[0]["replacement_date"]
                wear_level, remaining_pct = calculate_wear_level(
                    last_replacement, useful_life_months
                )
                procurement_deadline = calculate_procurement_deadline(
                    last_replacement, useful_life_months, procurement_time_days
                )
            else:
                wear_level = "red"
                remaining_pct = 0
                procurement_deadline = None

            result.append(
                {
                    "equipment_name": equipment_name,
                    "part_name": part_name,
                    "total_needed": total_needed,
                    "qty_in_stock": qty_in_stock,
                    "wear_level": wear_level,
                    "remaining_pct": remaining_pct,
                    "procurement_deadline": procurement_deadline,
                    "procurement_time_days": procurement_time_days,
                }
            )

    return pd.DataFrame(result)
