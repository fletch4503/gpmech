from sqlalchemy.orm import Session
from database import Equipment, Workshop, SparePart, ReplacementRecord
from typing import List, Optional
from datetime import datetime


# CRUD для Equipment
def create_equipment(
    db: Session, name: str, qty_in_fleet: int, vin: Optional[str] = None
) -> Equipment:
    db_equipment = Equipment(name=name, qty_in_fleet=qty_in_fleet, vin=vin)
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def get_equipment(db: Session, equipment_id: int) -> Optional[Equipment]:
    return db.query(Equipment).filter(Equipment.id == equipment_id).first()


def get_equipment_by_name(db: Session, name: str) -> Optional[Equipment]:
    return db.query(Equipment).filter(Equipment.name == name).first()


def get_all_equipment(db: Session) -> List[Equipment]:
    return db.query(Equipment).all()


def update_equipment(
    db: Session,
    equipment_id: int,
    name: Optional[str] = None,
    qty_in_fleet: Optional[int] = None,
    vin: Optional[str] = None,
) -> Optional[Equipment]:
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if equipment:
        if name is not None:
            equipment.name = name
        if qty_in_fleet is not None:
            equipment.qty_in_fleet = qty_in_fleet
        if vin is not None:
            equipment.vin = vin
        db.commit()
        db.refresh(equipment)
    return equipment


def delete_equipment(db: Session, equipment_id: int) -> bool:
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if equipment:
        db.delete(equipment)
        db.commit()
        return True
    return False


# CRUD для Workshop
def create_workshop(db: Session, name: str, address: str) -> Workshop:
    db_workshop = Workshop(name=name, address=address)
    db.add(db_workshop)
    db.commit()
    db.refresh(db_workshop)
    return db_workshop


def get_all_workshops(db: Session) -> List[Workshop]:
    return db.query(Workshop).all()


# CRUD для SparePart
def create_spare_part(
    db: Session,
    name: str,
    useful_life_months: int,
    equipment_id: int,
    qty_per_equipment: int,
    qty_in_stock: int,
    procurement_time_days: int,
) -> SparePart:
    db_spare_part = SparePart(
        name=name,
        useful_life_months=useful_life_months,
        equipment_id=equipment_id,
        qty_per_equipment=qty_per_equipment,
        qty_in_stock=qty_in_stock,
        procurement_time_days=procurement_time_days,
    )
    db.add(db_spare_part)
    db.commit()
    db.refresh(db_spare_part)
    return db_spare_part


def get_spare_parts_by_equipment(db: Session, equipment_id: int) -> List[SparePart]:
    return db.query(SparePart).filter(SparePart.equipment_id == equipment_id).all()


def get_all_spare_parts(db: Session) -> List[SparePart]:
    return db.query(SparePart).all()


# CRUD для ReplacementRecord
def create_replacement_record(
    db: Session,
    equipment_id: int,
    spare_part_id: int,
    workshop_id: int,
    replacement_date: datetime,
    replacement_type: str,
    notes: Optional[str] = None,
) -> ReplacementRecord:
    db_replacement = ReplacementRecord(
        equipment_id=equipment_id,
        spare_part_id=spare_part_id,
        workshop_id=workshop_id,
        replacement_date=replacement_date,
        replacement_type=replacement_type,
        notes=notes,
    )
    db.add(db_replacement)
    db.commit()
    db.refresh(db_replacement)
    return db_replacement


def get_replacement_records_by_equipment(
    db: Session, equipment_id: int
) -> List[ReplacementRecord]:
    return (
        db.query(ReplacementRecord)
        .filter(ReplacementRecord.equipment_id == equipment_id)
        .all()
    )


def get_all_replacement_records(db: Session) -> List[ReplacementRecord]:
    return db.query(ReplacementRecord).all()


def update_replacement_record(
    db: Session,
    replacement_id: int,
    equipment_id: Optional[int] = None,
    spare_part_id: Optional[int] = None,
    workshop_id: Optional[int] = None,
    replacement_date: Optional[datetime] = None,
    replacement_type: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[ReplacementRecord]:
    replacement = (
        db.query(ReplacementRecord)
        .filter(ReplacementRecord.id == replacement_id)
        .first()
    )
    if replacement:
        if equipment_id is not None:
            replacement.equipment_id = equipment_id
        if spare_part_id is not None:
            replacement.spare_part_id = spare_part_id
        if workshop_id is not None:
            replacement.workshop_id = workshop_id
        if replacement_date is not None:
            replacement.replacement_date = replacement_date
        if replacement_type is not None:
            replacement.replacement_type = replacement_type
        if notes is not None:
            replacement.notes = notes
        db.commit()
        db.refresh(replacement)
    return replacement


def delete_replacement_record(db: Session, replacement_id: int) -> bool:
    replacement = (
        db.query(ReplacementRecord)
        .filter(ReplacementRecord.id == replacement_id)
        .first()
    )
    if replacement:
        db.delete(replacement)
        db.commit()
        return True
    return False
