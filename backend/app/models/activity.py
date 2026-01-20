from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_activity_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Activity details
    name: Mapped[str] = mapped_column(String(300))
    activity_type: Mapped[str] = mapped_column(String(50))  # Ride, Run, VirtualRide, etc.
    sport_type: Mapped[str | None] = mapped_column(String(50))  # More specific type
    start_date: Mapped[datetime] = mapped_column(DateTime)

    # Stats
    distance: Mapped[float] = mapped_column(Float, default=0)  # meters
    moving_time: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    elapsed_time: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    total_elevation_gain: Mapped[float | None] = mapped_column(Float)
    average_speed: Mapped[float | None] = mapped_column(Float)
    max_speed: Mapped[float | None] = mapped_column(Float)

    # Equipment
    gear_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"))
    strava_gear_id: Mapped[str | None] = mapped_column(String(50))  # Original Strava gear ID

    # Flags and metadata
    trainer: Mapped[bool] = mapped_column(Boolean, default=False)
    commute: Mapped[bool] = mapped_column(Boolean, default=False)
    manual: Mapped[bool] = mapped_column(Boolean, default=False)
    private: Mapped[bool] = mapped_column(Boolean, default=False)

    # External info (for detecting Zwift, TrainerRoad, etc.)
    external_id: Mapped[str | None] = mapped_column(String(200))
    device_name: Mapped[str | None] = mapped_column(String(200))

    # Timestamps
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="activities")
    gear = relationship("Equipment", back_populates="activities")
