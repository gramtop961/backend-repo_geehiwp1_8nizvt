import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Property, Booking
from bson import ObjectId


app = FastAPI(title="Villas & Farmhouses Rental API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IDResponse(BaseModel):
    id: str


def serialize_doc(doc: dict):
    if not doc:
        return doc
    result = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


@app.get("/")
def read_root():
    return {"message": "Villas & Farmhouses Rental API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Properties Endpoints
@app.get("/api/properties")
def list_properties(
    q: Optional[str] = None,
    property_type: Optional[str] = Query(None, alias="type"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    guests: Optional[int] = None,
    amenity: Optional[str] = None,
    limit: Optional[int] = Query(12, ge=1, le=50),
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    flt = {}
    if q:
        flt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"location": {"$regex": q, "$options": "i"}},
            {"country": {"$regex": q, "$options": "i"}},
        ]
    if property_type:
        flt["property_type"] = {"$regex": f"^{property_type}$", "$options": "i"}
    price_range = {}
    if min_price is not None:
        price_range["$gte"] = float(min_price)
    if max_price is not None:
        price_range["$lte"] = float(max_price)
    if price_range:
        flt["price_per_night"] = price_range
    if bedrooms is not None:
        flt["bedrooms"] = {"$gte": bedrooms}
    if guests is not None:
        flt["max_guests"] = {"$gte": guests}
    if amenity:
        flt["amenities"] = {"$in": [amenity]}

    docs = get_documents("property", flt, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/properties/featured")
def featured_properties(limit: int = Query(8, ge=1, le=24)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("property", {}, limit)
    return [serialize_doc(d) for d in docs]


@app.post("/api/properties", response_model=IDResponse)
def create_property(prop: Property):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    new_id = create_document("property", prop)
    return {"id": new_id}


@app.get("/api/properties/{property_id}")
def get_property(property_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["property"].find_one({"_id": ObjectId(property_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Property not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")


# Bookings
@app.post("/api/bookings", response_model=IDResponse)
def create_booking(b: Booking):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    booking_id = create_document("booking", b)
    return {"id": booking_id}


# Simple seed route for demo (optional)
class SeedResponse(BaseModel):
    inserted: int


@app.post("/api/seed", response_model=SeedResponse)
def seed_properties():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # If we already have at least 10 properties, skip
    count = db["property"].count_documents({})
    if count >= 10:
        return {"inserted": 0}

    samples: List[Property] = [
        Property(
            title="Skyline Luxe Villa",
            description="A luxurious villa with panoramic city views and infinity pool.",
            property_type="villa",
            location="Mumbai",
            country="India",
            price_per_night=420,
            max_guests=8,
            bedrooms=4,
            bathrooms=3,
            amenities=["Pool", "WiFi", "Chef", "Parking", "Garden"],
            images=[
                "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d98",
                "https://images.unsplash.com/photo-1499951360447-b19be8fe80f5",
            ],
            host={"name": "Anaya Kapoor", "email": "anaya@example.com"},
        ),
        Property(
            title="Serene Farm Retreat",
            description="Peaceful farmhouse surrounded by lush fields and a private orchard.",
            property_type="farmhouse",
            location="Pune",
            country="India",
            price_per_night=220,
            max_guests=6,
            bedrooms=3,
            bathrooms=2,
            amenities=["Bonfire", "WiFi", "Parking", "Pet Friendly"],
            images=[
                "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
            ],
            host={"name": "Rohit Verma", "email": "rohit@example.com"},
        ),
        Property(
            title="Modern Glass House",
            description="Contemporary glass house tucked in the hills with stunning sunsets.",
            property_type="villa",
            location="Lonavala",
            country="India",
            price_per_night=350,
            max_guests=5,
            bedrooms=2,
            bathrooms=2,
            amenities=["Mountain View", "WiFi", "Hot Tub"],
            images=[
                "https://images.unsplash.com/photo-1494526585095-c41746248156",
                "https://images.unsplash.com/photo-1499696010189-9d2150aee9f6",
            ],
            host={"name": "Mira Shah", "email": "mira@example.com"},
        ),
        Property(
            title="Coastal Breeze Villa",
            description="Minimal, modern villa steps from a quiet beach with sea breeze.",
            property_type="villa",
            location="Goa",
            country="India",
            price_per_night=300,
            max_guests=7,
            bedrooms=3,
            bathrooms=3,
            amenities=["Beach Access", "Pool", "AC", "WiFi"],
            images=[
                "https://images.unsplash.com/photo-1475855581690-80accde3ae2b",
                "https://images.unsplash.com/photo-1505692794403-34fdb2f1faac",
            ],
            host={"name": "Elena Dsouza", "email": "elena@example.com"},
        ),
        Property(
            title="Riverside Farmhouse",
            description="Charming farmhouse along a riverside with sprawling lawns.",
            property_type="farmhouse",
            location="Karjat",
            country="India",
            price_per_night=180,
            max_guests=6,
            bedrooms=3,
            bathrooms=2,
            amenities=["Bonfire", "Parking", "Pet Friendly", "BBQ"],
            images=[
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
                "https://images.unsplash.com/photo-1460317442991-0ec209397118",
            ],
            host={"name": "Dev Patel", "email": "dev@example.com"},
        ),
        Property(
            title="Forest Edge Cottage",
            description="Cozy cottage at the forest edge; perfect for quiet retreats.",
            property_type="cottage",
            location="Coorg",
            country="India",
            price_per_night=160,
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            amenities=["Fireplace", "Mountain View", "WiFi"],
            images=[
                "https://images.unsplash.com/photo-1441974231531-c6227db76b6e",
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
            ],
            host={"name": "Aarav Nair", "email": "aarav@example.com"},
        ),
        Property(
            title="Royal Heritage Mansion",
            description="Grand mansion restored with modern comforts and private courtyard.",
            property_type="mansion",
            location="Jaipur",
            country="India",
            price_per_night=550,
            max_guests=10,
            bedrooms=6,
            bathrooms=5,
            amenities=["Chef", "Butler", "WiFi", "Parking", "Garden"],
            images=[
                "https://images.unsplash.com/photo-1501183638710-841dd1904471",
                "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d98",
            ],
            host={"name": "Rani Singh", "email": "rani@example.com"},
        ),
        Property(
            title="Cliffside Infinity Villa",
            description="Perched on a cliff with a dramatic infinity pool and sunset views.",
            property_type="villa",
            location="Visakhapatnam",
            country="India",
            price_per_night=480,
            max_guests=8,
            bedrooms=4,
            bathrooms=4,
            amenities=["Infinity Pool", "WiFi", "AC", "Chef"],
            images=[
                "https://images.unsplash.com/photo-1455587734955-081b22074882",
                "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            ],
            host={"name": "Kabir Rao", "email": "kabir@example.com"},
        ),
        Property(
            title="Vineyard Country House",
            description="Country farmhouse overlooking vineyards with rustic-chic interiors.",
            property_type="farmhouse",
            location="Nashik",
            country="India",
            price_per_night=210,
            max_guests=5,
            bedrooms=3,
            bathrooms=2,
            amenities=["Winery Tour", "Bonfire", "WiFi"],
            images=[
                "https://images.unsplash.com/photo-1496417263034-38ec4f0b665a",
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
            ],
            host={"name": "Neha Kulkarni", "email": "neha@example.com"},
        ),
        Property(
            title="Lakeside Minimal Villa",
            description="Ultra-minimal lakeside villa with floor-to-ceiling glass.",
            property_type="villa",
            location="Udaipur",
            country="India",
            price_per_night=390,
            max_guests=6,
            bedrooms=3,
            bathrooms=3,
            amenities=["Lake View", "WiFi", "Parking", "Chef"],
            images=[
                "https://images.unsplash.com/photo-1484154218962-a197022b5858",
                "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d98",
            ],
            host={"name": "Ishaan Mehta", "email": "ishaan@example.com"},
        ),
        Property(
            title="Tea Estate Bungalow",
            description="Colonial-era bungalow nestled within a working tea estate.",
            property_type="cottage",
            location="Munnar",
            country="India",
            price_per_night=190,
            max_guests=5,
            bedrooms=3,
            bathrooms=2,
            amenities=["Garden", "WiFi", "Bonfire"],
            images=[
                "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d98",
                "https://images.unsplash.com/photo-1449844908441-8829872d2607",
            ],
            host={"name": "Priya Iyer", "email": "priya@example.com"},
        ),
        Property(
            title="Desert Dune Villa",
            description="Stark, sculptural villa opening to desert dunes and starry skies.",
            property_type="villa",
            location="Jaisalmer",
            country="India",
            price_per_night=260,
            max_guests=6,
            bedrooms=3,
            bathrooms=2,
            amenities=["Rooftop", "WiFi", "AC", "BBQ"],
            images=[
                "https://images.unsplash.com/photo-1519710164239-da123dc03ef4",
                "https://images.unsplash.com/photo-1499696010189-9d2150aee9f6",
            ],
            host={"name": "Zoya Khan", "email": "zoya@example.com"},
        ),
        Property(
            title="Himalayan View Chalet",
            description="Warm wooden chalet with sweeping Himalayan views and hot tub.",
            property_type="cottage",
            location="Manali",
            country="India",
            price_per_night=275,
            max_guests=6,
            bedrooms=3,
            bathrooms=2,
            amenities=["Mountain View", "Hot Tub", "Fireplace", "WiFi"],
            images=[
                "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd",
                "https://images.unsplash.com/photo-1502673530728-f79b4cab31b1",
            ],
            host={"name": "Arjun Malhotra", "email": "arjun@example.com"},
        ),
    ]

    inserted = 0
    for s in samples:
        create_document("property", s)
        inserted += 1
    return {"inserted": inserted}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
