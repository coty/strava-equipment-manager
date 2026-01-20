from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_gear_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Equipment details
    name: Mapped[str] = mapped_column(String(200))
    equipment_type: Mapped[str] = mapped_column(String(50))  # bike, shoes
    brand_name: Mapped[str | None] = mapped_column(String(100))
    model_name: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))

    # Stats
    distance: Mapped[float] = mapped_column(Float, default=0)  # in meters

    # Flags
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_retired: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="equipment")
    activities = relationship("Activity", back_populates="gear")
    rules = relationship("Rule", back_populates="target_gear")
