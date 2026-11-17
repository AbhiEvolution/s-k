from datetime import date, datetime, time
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.slots import as_utc, on_grid


class AvailabilityWindow(BaseModel):
    weekday: int = Field(ge=0, le=6, description="Monday=0 ... Sunday=6")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if not on_grid(self.start_time) or not on_grid(self.end_time):
            raise ValueError("times must sit on the slot grid (e.g. 09:00, 09:30)")
        return self

    model_config = ConfigDict(from_attributes=True)


class AvailabilityUpdate(BaseModel):
    windows: list[AvailabilityWindow] = Field(max_length=28)

    @model_validator(mode="after")
    def no_overlaps(self):
        for weekday in range(7):
            day = sorted((w for w in self.windows if w.weekday == weekday), key=lambda w: w.start_time)
            for first, second in zip(day, day[1:]):
                if second.start_time < first.end_time:
                    raise ValueError(f"overlapping windows on weekday {weekday}")
        return self


class AvailabilityResponse(BaseModel):
    doctor_id: int
    windows: list[AvailabilityWindow]


class SlotResponse(BaseModel):
    starts_at: datetime
    ends_at: datetime
    available: bool


class AppointmentCreate(BaseModel):
    clinic_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    # AwareDatetime rejects "2026-12-01T09:00:00" (no timezone): no guessing.
    starts_at: AwareDatetime
    reason: str | None = Field(default=None, max_length=255)


class AppointmentResponse(BaseModel):
    id: int
    clinic_id: int
    doctor_id: int
    patient_id: int
    starts_at: datetime
    ends_at: datetime
    status: Literal["booked", "cancelled"]
    reason: str | None
    created_by_user_id: int
    cancelled_at: datetime | None

    @field_validator("starts_at", "ends_at", "cancelled_at")
    @classmethod
    def utc(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None

    model_config = ConfigDict(from_attributes=True)


class SlotQuery(BaseModel):
    doctor_id: int
    day: date
