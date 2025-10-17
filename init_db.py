import os
from models import generate_test_data, create_dataframes

# Проверяем, включена ли поддержка базы данных
USE_DATABASE = os.getenv("USE_DATABASE", "true").lower() == "true"

if USE_DATABASE:
    from database import SessionLocal, create_tables
    from crud import (
        create_equipment_model,
        create_equipment,
        create_workshop,
        create_spare_part,
        create_replacement_record,
        get_equipment_model_by_name,
        get_equipment_by_vin,
        get_all_workshops,
        get_all_spare_parts,
    )
else:
    # Заглушки для режима без базы данных
    SessionLocal = None
    create_tables = None


def initialize_database():
    """Инициализация базы данных начальными данными"""
    if not USE_DATABASE:
        # Для режима без базы данных просто возвращаем тестовые данные
        print("Инициализация в режиме без базы данных...")
        return

    db = SessionLocal()
    try:
        # Создаем таблицы
        create_tables()

        # Проверяем, есть ли уже данные
        from crud import get_all_equipment_models

        if get_all_equipment_models(db):
            print("База данных уже инициализирована")
            return

        print("Инициализация базы данных начальными данными...")

        # Генерируем тестовые данные
        (
            equipment_models,
            equipment_instances,
            workshops,
            spare_parts,
            replacement_records,
        ) = generate_test_data()

        # Сохраняем модели оборудования
        for model in equipment_models:
            create_equipment_model(db, model.name, model.qty_in_fleet)

        # Сохраняем экземпляры оборудования
        for instance in equipment_instances:
            model = get_equipment_model_by_name(db, instance.model_name)
            if model:
                create_equipment(db, model.id, instance.vin)

        # Сохраняем мастерские
        for ws in workshops:
            create_workshop(db, ws.name, ws.address)

        # Сохраняем запчасти
        for sp in spare_parts:
            model = get_equipment_model_by_name(db, sp.parent_equipment)
            if model:
                create_spare_part(
                    db,
                    sp.name,
                    sp.useful_life_months,
                    model.id,
                    sp.qty_per_equipment,
                    sp.qty_in_stock,
                    sp.procurement_time_days,
                )

        # Сохраняем записи о заменах
        for rr in replacement_records:
            equipment = get_equipment_by_vin(db, rr.equipment_name)
            spare_part = None
            for sp in get_all_spare_parts(db):
                if sp.name == rr.spare_part_name:
                    spare_part = sp
                    break
            workshop = None
            for ws in get_all_workshops(db):
                if ws.name == rr.workshop_name:
                    workshop = ws
                    break

            if equipment and spare_part and workshop:
                create_replacement_record(
                    db,
                    equipment.id,
                    spare_part.id,
                    workshop.id,
                    rr.replacement_date,
                    rr.replacement_type,
                    rr.notes,
                )

        print("База данных успешно инициализирована!")

    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
