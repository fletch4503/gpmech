from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    # Float,
    ForeignKey,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gpmech_user:gpmech_pass@localhost:5432/gpmech"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class EquipmentModel(Base):
    __tablename__ = "equipment_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String, unique=True, index=True
    )  # Название модели (например, "Экскаватор CAT 320")
    qty_in_fleet = Column(Integer)  # Общее количество в парке

    # Отношения
    equipment_instances = relationship("Equipment", back_populates="model")
    spare_parts = relationship("SparePart", back_populates="equipment_model")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("equipment_models.id"))
    vin = Column(
        String, unique=True, index=True
    )  # Уникальный VIN номер для каждого экземпляра

    # Отношения
    model = relationship("EquipmentModel", back_populates="equipment_instances")
    replacements = relationship("ReplacementRecord", back_populates="equipment")


class Workshop(Base):
    __tablename__ = "workshops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String)

    # Отношения
    replacements = relationship("ReplacementRecord", back_populates="workshop")


class SparePart(Base):
    __tablename__ = "spare_parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    useful_life_months = Column(Integer)
    equipment_model_id = Column(Integer, ForeignKey("equipment_models.id"))
    qty_per_equipment = Column(Integer)
    qty_in_stock = Column(Integer)
    procurement_time_days = Column(Integer)

    # Отношения
    equipment_model = relationship("EquipmentModel", back_populates="spare_parts")
    replacements = relationship("ReplacementRecord", back_populates="spare_part")


class ReplacementRecord(Base):
    __tablename__ = "replacement_records"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    spare_part_id = Column(Integer, ForeignKey("spare_parts.id"))
    workshop_id = Column(Integer, ForeignKey("workshops.id"))
    replacement_date = Column(DateTime)
    replacement_type = Column(String)  # 'repair', 'scheduled', 'unscheduled'
    notes = Column(Text, nullable=True)

    # Отношения
    equipment = relationship("Equipment", back_populates="replacements")
    spare_part = relationship("SparePart", back_populates="replacements")
    workshop = relationship("Workshop", back_populates="replacements")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
