from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Rule details
    name: Mapped[str] = mapped_column(String(200))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    target_gear_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="rules")
    target_gear = relationship("Equipment", back_populates="rules")
    conditions = relationship("RuleCondition", back_populates="rule", cascade="all, delete-orphan")


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"))

    # Condition details
    field: Mapped[str] = mapped_column(String(50))  # name, activity_type, trainer, etc.
    operator: Mapped[str] = mapped_column(String(50))  # equals, contains, starts_with, etc.
    value: Mapped[str] = mapped_column(String(500))
    logic: Mapped[str] = mapped_column(String(10), default="AND")  # AND, OR

    # Relationships
    rule = relationship("Rule", back_populates="conditions")
