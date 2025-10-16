import pandas as pd
from datetime import datetime, timedelta
import random

# Определение структур данных


class SparePart:
    def __init__(
        self,
        name,
        useful_life_months,
        parent_equipment,
        qty_per_equipment,
        qty_in_stock,
        procurement_time_days,
    ):
        self.name = name
        self.useful_life_months = useful_life_months
        self.parent_equipment = parent_equipment
        self.qty_per_equipment = qty_per_equipment
        self.qty_in_stock = qty_in_stock
        self.procurement_time_days = procurement_time_days


class Equipment:
    def __init__(self, name, qty_in_fleet):
        self.name = name
        self.qty_in_fleet = qty_in_fleet


class Workshop:
    def __init__(self, name, address):
        self.name = name
        self.address = address


class ReplacementRecord:
    def __init__(
        self,
        equipment_name,
        spare_part_name,
        workshop_name,
        replacement_date,
        replacement_type,
        notes="",
    ):
        self.equipment_name = equipment_name
        self.spare_part_name = spare_part_name
        self.workshop_name = workshop_name
        self.replacement_date = replacement_date
        self.replacement_type = replacement_type  # 'repair', 'scheduled', 'unscheduled'
        self.notes = notes


# Генерация тестовых данных


def generate_test_data():
    # Оборудование
    equipment_list = [
        Equipment("Экскаватор CAT 320", 5),
        Equipment("Бульдозер D6", 3),
        Equipment("Самосвал Volvo FH16", 8),
        Equipment("Кран Liebherr LTM", 2),
        Equipment("Генератор Cummins", 4),
        Equipment("Компрессор Atlas Copco", 6),
    ]

    # Мастерские
    workshops = [
        Workshop("Авторемонтная мастерская №1", "ул. Ленина, 10"),
        Workshop("Сервисный центр ТехноСервис", "пр. Победы, 25"),
        Workshop("Мастерская РемонтАвто", "ул. Гагарина, 5"),
        Workshop("Центр технического обслуживания", "ул. Кирова, 15"),
        Workshop("Автосервис Профи", "ул. Советская, 30"),
        Workshop("Мастерская СпецТех", "ул. Московская, 20"),
    ]

    # Запчасти
    spare_parts = [
        SparePart("Фильтр гидравлический", 24, "Экскаватор CAT 320", 4, 20, 7),
        SparePart("Масляный фильтр", 12, "Бульдозер D6", 2, 15, 5),
        SparePart("Топливный насос", 36, "Самосвал Volvo FH16", 1, 10, 14),
        SparePart("Гидроцилиндр", 48, "Кран Liebherr LTM", 6, 12, 21),
        SparePart("Аккумулятор", 24, "Генератор Cummins", 2, 10, 3),
        SparePart("Ремень генератора", 18, "Компрессор Atlas Copco", 1, 25, 4),
        SparePart("Шина", 24, "Экскаватор CAT 320", 4, 16, 10),
        SparePart("Тормозные колодки", 12, "Самосвал Volvo FH16", 8, 40, 6),
        SparePart("Цепь привода", 36, "Бульдозер D6", 1, 5, 18),
        SparePart("Клапан давления", 30, "Кран Liebherr LTM", 2, 8, 12),
        SparePart("Шина", 24, "Самосвал Volvo FH16", 6, 18, 14),
    ]

    # Записи о заменах
    replacement_records = []
    base_date = datetime.now() - timedelta(days=365)

    for i in range(30):
        equipment = random.choice(equipment_list)
        # Выбираем запчасть, подходящую для этого оборудования
        suitable_parts = [
            sp for sp in spare_parts if sp.parent_equipment == equipment.name
        ]
        if suitable_parts:
            spare_part = random.choice(suitable_parts)
            workshop = random.choice(workshops)
            replacement_date = base_date + timedelta(days=random.randint(0, 365))
            replacement_type = random.choice(["repair", "scheduled", "unscheduled"])
            notes = f"Замена запчасти {spare_part.name} в {equipment.name}"
            replacement_records.append(
                ReplacementRecord(
                    equipment.name,
                    spare_part.name,
                    workshop.name,
                    replacement_date,
                    replacement_type,
                    notes,
                )
            )

    return equipment_list, workshops, spare_parts, replacement_records


# Преобразование в DataFrames для удобства работы
def create_dataframes(equipment_list, workshops, spare_parts, replacement_records):
    equipment_df = pd.DataFrame(
        [{"name": eq.name, "qty_in_fleet": eq.qty_in_fleet} for eq in equipment_list]
    )

    workshops_df = pd.DataFrame(
        [{"name": ws.name, "address": ws.address} for ws in workshops]
    )

    spare_parts_df = pd.DataFrame(
        [
            {
                "name": sp.name,
                "useful_life_months": sp.useful_life_months,
                "parent_equipment": sp.parent_equipment,
                "qty_per_equipment": sp.qty_per_equipment,
                "qty_in_stock": sp.qty_in_stock,
                "procurement_time_days": sp.procurement_time_days,
            }
            for sp in spare_parts
        ]
    )

    replacements_df = pd.DataFrame(
        [
            {
                "equipment_name": rr.equipment_name,
                "spare_part_name": rr.spare_part_name,
                "workshop_name": rr.workshop_name,
                "replacement_date": rr.replacement_date,
                "replacement_type": rr.replacement_type,
                "notes": rr.notes,
            }
            for rr in replacement_records
        ]
    )

    return equipment_df, workshops_df, spare_parts_df, replacements_df
