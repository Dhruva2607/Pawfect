"""
Pydantic v2 schemas for Shelter (Adoption Center) accounts and profiles.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Shelter(BaseModel):
    """Full Shelter document stored in MongoDB `shelters` collection."""
    id: str = Field(alias="_id")
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=3)
    password_hash: str
    contact_phone: str = Field(..., min_length=5, max_length=40)
    address: str = Field(..., min_length=2, max_length=200)
    city: str = Field(..., min_length=2, max_length=80)
    state: str = Field(..., min_length=2, max_length=80)
    country: str = Field(default="India", min_length=2, max_length=80)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    description: Optional[str] = Field(None, max_length=2000)
    logo_url: Optional[str] = None
    website: Optional[str] = None
    operating_hours: Optional[str] = Field(None, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)
    verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }


class ShelterResponse(BaseModel):
    """Public / authenticated shelter profile without password_hash."""
    id: str = Field(alias="_id")
    name: str
    email: str
    contact_phone: str
    address: str
    city: str
    state: str
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    operating_hours: Optional[str] = None
    registration_number: Optional[str] = None
    verified: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
    }


class ShelterSignupRequest(BaseModel):
    """Request payload for shelter registration."""
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6, max_length=128)
    contact_phone: str = Field(..., min_length=5, max_length=40)
    address: str = Field(..., min_length=2, max_length=200)
    city: str = Field(..., min_length=2, max_length=80)
    state: str = Field(..., min_length=2, max_length=80)
    country: str = Field(default="India", min_length=2, max_length=80)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    description: Optional[str] = Field(None, max_length=2000)
    logo_url: Optional[str] = None
    website: Optional[str] = None
    operating_hours: Optional[str] = Field(None, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)


class ShelterLoginRequest(BaseModel):
    """Request payload for shelter login."""
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class ShelterUpdateRequest(BaseModel):
    """Partial update payload for shelter profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    contact_phone: Optional[str] = Field(None, min_length=5, max_length=40)
    address: Optional[str] = Field(None, min_length=2, max_length=200)
    city: Optional[str] = Field(None, min_length=2, max_length=80)
    state: Optional[str] = Field(None, min_length=2, max_length=80)
    country: Optional[str] = Field(None, min_length=2, max_length=80)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    description: Optional[str] = Field(None, max_length=2000)
    logo_url: Optional[str] = None
    website: Optional[str] = None
    operating_hours: Optional[str] = Field(None, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)


class ShelterAuthResponse(BaseModel):
    """Auth response containing signed JWT and shelter profile."""
    token: str
    role: str = "shelter"
    shelter: ShelterResponse
