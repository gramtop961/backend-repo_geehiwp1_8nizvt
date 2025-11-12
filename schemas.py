"""
Database Schemas for Villa & Farmhouse Rental App

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercase of the class name (e.g., Property -> "property").
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class Host(BaseModel):
    name: str = Field(..., description="Host full name")
    email: EmailStr = Field(..., description="Host contact email")
    phone: Optional[str] = Field(None, description="Host phone number")


class Property(BaseModel):
    title: str = Field(..., description="Listing title")
    description: Optional[str] = Field(None, description="Detailed description")
    property_type: str = Field(..., description="villa | farmhouse | cottage | mansion")
    location: str = Field(..., description="City/Area name")
    country: str = Field(..., description="Country")
    price_per_night: float = Field(..., ge=0, description="Nightly rate in USD")
    max_guests: int = Field(..., ge=1, description="Maximum number of guests")
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    amenities: List[str] = Field(default_factory=list, description="List of amenities")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    host: Host = Field(..., description="Host details")


class Booking(BaseModel):
    property_id: str = Field(..., description="ID of the property being booked")
    guest_name: str = Field(..., description="Guest full name")
    guest_email: EmailStr = Field(..., description="Guest email")
    check_in: str = Field(..., description="ISO date (YYYY-MM-DD)")
    check_out: str = Field(..., description="ISO date (YYYY-MM-DD)")
    guests: int = Field(..., ge=1, description="Number of guests")
    total_price: float = Field(..., ge=0)


# Example additional schemas (kept for reference of viewer; not used directly)
class User(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True
