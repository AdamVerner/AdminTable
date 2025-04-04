import random
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import relationship

from .base import Base, SessionLocal, engine


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")

    created_at = Column(DateTime, default=datetime.now, server_default=func.now())


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    public = Column(Boolean, default=True)

    owner = relationship("User", back_populates="items")


async def generate_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        session.add(u1 := User(email=f"{random.randint(10, 10**10)}@email.local"))
        session.add(u2 := User(email=f"{random.randint(10, 10**10)}@email.local"))
        await session.flush()
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id))
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id, public=False))
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id, public=False))
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
        session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
        session.add(Item(title=f"item {random.randint(10, 10**10)}"))
        session.add(Item(title=f"item {random.randint(10, 10**10)}"))
        session.add(Item(title=f"other item {random.randint(10, 10**10)}", owner_id=u2.id, public=False))
        await session.commit()

    print("Data generated")


async def teardown_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
