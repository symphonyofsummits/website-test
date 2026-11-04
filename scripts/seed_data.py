"""
Seed real Himalayan treks + batches + an admin user.
Run:  python -m scripts.seed_data
"""
import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import session_scope
from app.models import Batch, Trip, User
from app.models.enums import (
    BatchStatus, Difficulty, TripCategory, TripScope, UserRole,
)

TRIPS = [
    dict(
        slug="hampta-pass-trek", title="Hampta Pass Trek",
        subtitle="Contrasting landscapes, alpine camps, dramatic pass crossing",
        category=TripCategory.TREK, scope=TripScope.INDIAN, difficulty=Difficulty.MODERATE,
        region="Himachal Pradesh", state="Himachal Pradesh",
        duration_days=5, max_altitude_m=4270, trek_distance_km=Decimal("26.0"),
        base_price=Decimal("12499"), advance_amount=Decimal("2000"),
        base_camp="Manali",
        inclusions=["Meals during trek", "Camping charges", "Trekking permits", "Qualified guide"],
        exclusions=["Travel to/from Manali", "Personal expenses", "Insurance"],
        highlights=["Dramatic pass crossing at 4270m", "Chandratal Lake visit", "Mix of green & arid landscapes"],
        is_published=True, is_featured=True,
        cover_image="https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1200&q=80",
    ),
    dict(
        slug="goechala-trek", title="Goechala Trek",
        subtitle="High Himalayan views of Kanchenjunga",
        category=TripCategory.TREK, scope=TripScope.INDIAN, difficulty=Difficulty.DIFFICULT,
        region="Sikkim", state="Sikkim",
        duration_days=8, max_altitude_m=4940, trek_distance_km=Decimal("90.0"),
        base_price=Decimal("18999"), advance_amount=Decimal("3000"),
        base_camp="Yuksom",
        highlights=["Sunrise view of Kanchenjunga", "Dzongri meadows", "Samiti Lake"],
        is_published=True, is_featured=True,
        cover_image="https://images.unsplash.com/photo-1533130061792-64b345e4a833?auto=format&fit=crop&w=1200&q=80",
    ),
    dict(
        slug="markha-valley-trek", title="Markha Valley Trek",
        subtitle="Cold desert, remote villages, wide-open Ladakh",
        category=TripCategory.TREK, scope=TripScope.INDIAN, difficulty=Difficulty.DIFFICULT,
        region="Ladakh", state="Ladakh",
        duration_days=7, max_altitude_m=5200, trek_distance_km=Decimal("75.0"),
        base_price=Decimal("16499"), advance_amount=Decimal("3000"),
        base_camp="Leh",
        is_published=True, is_featured=True,
        cover_image="https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
    ),
    dict(
        slug="kedarkantha-winter-trek", title="Kedarkantha Winter Trek",
        subtitle="Classic Indian winter trek with snow summit",
        category=TripCategory.TREK, scope=TripScope.INDIAN, difficulty=Difficulty.EASY,
        region="Uttarakhand", state="Uttarakhand",
        duration_days=6, max_altitude_m=3810, trek_distance_km=Decimal("20.0"),
        base_price=Decimal("8999"), advance_amount=Decimal("1500"),
        is_published=True,
        cover_image="https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1200&q=80",
    ),
    dict(
        slug="everest-base-camp", title="Everest Base Camp Trek",
        subtitle="The classic Himalayan pilgrimage of trekkers",
        category=TripCategory.TREK, scope=TripScope.INTERNATIONAL, difficulty=Difficulty.DIFFICULT,
        region="Nepal", country="Nepal", state="Khumbu",
        duration_days=14, max_altitude_m=5364,
        base_price=Decimal("89999"), advance_amount=Decimal("10000"),
        base_camp="Lukla",
        is_published=True, is_featured=True,
    ),
    dict(
        slug="chardham-yatra", title="Char Dham Yatra by Road",
        subtitle="Yamunotri · Gangotri · Kedarnath · Badrinath",
        category=TripCategory.PILGRIMAGE, scope=TripScope.INDIAN, difficulty=Difficulty.EASY,
        region="Uttarakhand", state="Uttarakhand",
        duration_days=11, base_price=Decimal("32999"), advance_amount=Decimal("5000"),
        is_published=True,
    ),
    dict(
        slug="stok-kangri-expedition", title="Stok Kangri Expedition",
        subtitle="6153m beginner-friendly Himalayan peak",
        category=TripCategory.EXPEDITION, scope=TripScope.INDIAN, difficulty=Difficulty.EXTREME,
        region="Ladakh", state="Ladakh",
        duration_days=10, max_altitude_m=6153,
        base_price=Decimal("45999"), advance_amount=Decimal("8000"),
        technical_grade="Alpine F+",
        is_published=True,
    ),
    dict(
        slug="kilimanjaro-expedition", title="Mt. Kilimanjaro — Machame Route",
        subtitle="Africa's highest peak, 5895m",
        category=TripCategory.EXPEDITION, scope=TripScope.INTERNATIONAL, difficulty=Difficulty.DIFFICULT,
        region="Tanzania", country="Tanzania",
        duration_days=9, max_altitude_m=5895,
        base_price=Decimal("185000"), advance_amount=Decimal("25000"),
        is_published=True,
    ),
]


async def main():
    async with session_scope() as db:
        # Admin user
        admin = (await db.execute(select(User).where(User.email == "admin@symphonyofsummits.com"))).scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@symphonyofsummits.com",
                phone="+919999999999",
                full_name="Symphony of Summits Admin",
                role=UserRole.SUPER_ADMIN,
                email_verified_at=date.today(),
            )
            db.add(admin)
            await db.flush()
            print("✓ Admin created:", admin.email)

        # Trips
        for payload in TRIPS:
            existing = (await db.execute(select(Trip).where(Trip.slug == payload["slug"]))).scalar_one_or_none()
            if existing:
                print(f"- skip (exists): {payload['slug']}")
                continue
            trip = Trip(**payload, created_by=admin.id)
            db.add(trip)
            await db.flush()
            print(f"✓ Trip: {trip.title}")

            # Create 4 upcoming monthly batches per trip
            for i in range(1, 5):
                start = date.today() + timedelta(days=30 * i)
                end = start + timedelta(days=trip.duration_days - 1)
                db.add(Batch(
                    trip_id=trip.id,
                    start_date=start,
                    end_date=end,
                    total_seats=15,
                    booked_seats=0,
                    reserved_seats=0,
                    status=BatchStatus.OPEN,
                ))
            print(f"  + 4 batches scheduled")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(main())
