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


class EquipmentModel:
    def __init__(self, name, qty_in_fleet):
        self.name = name
        self.qty_in_fleet = qty_in_fleet
        self.equipment_instances = []  # Список экземпляров оборудования


class Equipment:
    def __init__(self, model_name, vin):
        self.model_name = model_name
        self.vin = vin


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
    # Модели оборудования - расширить до 10 моделей
    equipment_models = [
        EquipmentModel("Экскаватор CAT 320", 5),
        EquipmentModel("Бульдозер D6", 3),
        EquipmentModel("Самосвал Volvo FH16", 8),
        EquipmentModel("Кран Liebherr LTM", 2),
        EquipmentModel("Генератор Cummins", 4),
        EquipmentModel("Компрессор Atlas Copco", 6),
        EquipmentModel("Погрузчик JCB", 7),
        EquipmentModel("Бетономешалка Putzmeister", 4),
        EquipmentModel("Автокран Grove", 3),
        EquipmentModel("Дизель-генератор Caterpillar", 5),
    ]

    # Создаем экземпляры оборудования для каждой модели
    equipment_instances = []
    for model in equipment_models:
        for i in range(model.qty_in_fleet):
            vin = f"{model.name.replace(' ', '').upper()}VIN{i+1:03d}"
            equipment_instances.append(Equipment(model.name, vin))
            model.equipment_instances.append(equipment_instances[-1])

    # Мастерские - расширить до 8-ми
    workshops = [
        Workshop("Авторемонтная мастерская №1", "ул. Ленина, 10"),
        Workshop("Сервисный центр ТехноСервис", "пр. Победы, 25"),
        Workshop("Мастерская РемонтАвто", "ул. Гагарина, 5"),
        Workshop("Центр технического обслуживания", "ул. Кирова, 15"),
        Workshop("Автосервис Профи", "ул. Советская, 30"),
        Workshop("Мастерская СпецТех", "ул. Московская, 20"),
        Workshop("СервисЦентр АвтоПро", "пр. Ленина, 45"),
        Workshop("Технический центр РемСервис", "ул. Пушкина, 12"),
    ]

    # Запчасти с разными сроками службы для покрытия всех зон износа
    spare_parts = [
        # Зеленая зона (новые запчасти, недавно замененные)
        SparePart("Фильтр гидравлический", 24, "Экскаватор CAT 320", 4, 20, 7),
        SparePart("Масляный фильтр", 12, "Бульдозер D6", 2, 15, 5),
        SparePart("Топливный насос", 36, "Самосвал Volvo FH16", 1, 10, 14),
        SparePart("Гидроцилиндр", 48, "Кран Liebherr LTM", 6, 12, 21),
        SparePart("Аккумулятор", 24, "Генератор Cummins", 2, 10, 3),
        SparePart("Ремень генератора", 18, "Компрессор Atlas Copco", 1, 25, 4),
        # Желтая зона (средний износ) - добавить 7 единиц
        SparePart("Шина", 24, "Экскаватор CAT 320", 4, 16, 10),
        SparePart("Тормозные колодки", 12, "Самосвал Volvo FH16", 8, 40, 6),
        SparePart("Цепь привода", 36, "Бульдозер D6", 1, 5, 18),
        SparePart("Водяной насос", 30, "Погрузчик JCB", 2, 8, 12),
        SparePart("Система охлаждения", 42, "Бетономешалка Putzmeister", 1, 3, 15),
        SparePart("Гидравлический мотор", 48, "Автокран Grove", 3, 6, 20),
        SparePart("Топливный фильтр", 18, "Дизель-генератор Caterpillar", 2, 12, 8),
        # Красная зона (критический износ) - добавить 5 единиц
        SparePart("Клапан давления", 30, "Кран Liebherr LTM", 2, 8, 12),
        SparePart("Шина", 24, "Самосвал Volvo FH16", 6, 18, 14),
        SparePart("Турбокомпрессор", 60, "Самосвал Volvo FH16", 1, 2, 30),
        SparePart("Гидронасос", 42, "Экскаватор CAT 320", 2, 3, 20),
        SparePart("Стартер", 36, "Генератор Cummins", 1, 1, 18),
    ]

    # Записи о заменах для создания разных уровней износа
    replacement_records = []
    base_date = datetime.now() - timedelta(days=365)

    # Создаем замены для покрытия всех зон износа
    wear_scenarios = [
        # Зеленая зона - недавние замены
        (0, 30),  # 0-30 дней назад
        # Желтая зона - средний срок
        (60, 120),  # 60-120 дней назад
        # Красная зона - старые замены или отсутствие замен
        (150, 365),  # 150-365 дней назад
    ]

    for scenario_days, count in [(0, 15), (60, 12), (150, 18)]:
        for i in range(count):
            equipment = random.choice(equipment_instances)
            # Выбираем запчасть, подходящую для модели этого оборудования
            suitable_parts = [
                sp for sp in spare_parts if sp.parent_equipment == equipment.model_name
            ]
            if suitable_parts:
                spare_part = random.choice(suitable_parts)
                workshop = random.choice(workshops)
                # Создаем дату замены в соответствующем диапазоне
                days_ago = scenario_days + random.randint(
                    0, min(30, 365 - scenario_days)
                )
                replacement_date = datetime.now() - timedelta(days=days_ago)
                replacement_type = random.choice(["repair", "scheduled", "unscheduled"])
                notes = f"Замена запчасти {spare_part.name} в {equipment.model_name} (VIN: {equipment.vin})"
                replacement_records.append(
                    ReplacementRecord(
                        equipment.vin,  # Теперь используем VIN вместо названия модели
                        spare_part.name,
                        workshop.name,
                        replacement_date,
                        replacement_type,
                        notes,
                    )
                )

    return (
        equipment_models,
        equipment_instances,
        workshops,
        spare_parts,
        replacement_records,
    )


# Преобразование в DataFrames для удобства работы
def create_dataframes(
    equipment_models, equipment_instances, workshops, spare_parts, replacement_records
):
    equipment_df = pd.DataFrame(
        [
            {"name": model.name, "qty_in_fleet": model.qty_in_fleet}
            for model in equipment_models
        ]
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
                "equipment_vin": rr.equipment_name,  # Теперь это VIN
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
