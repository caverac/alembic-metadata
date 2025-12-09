#!/usr/bin/env python
"""
Demonstrates the problem with SQLAlchemy Metadata.schema not updating table keys.

When you define models with DeclarativeBase, the table names are registered
in metadata.tables at class definition time. Setting metadata.schema AFTER
the models are defined does NOT retroactively update the table keys.
"""
from uuid import uuid4, UUID

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for models."""

    metadata = MetaData()


class Test(Base):
    """Test model."""

    __tablename__ = "test"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)


def main() -> None:
    """Demonstrate the metadata schema problem."""
    print("=" * 60)
    print("DEMONSTRATING THE PROBLEM")
    print("=" * 60)

    print("\n1. Initial state (no schema set):")
    print(f"   metadata.schema: {Base.metadata.schema!r}")
    print(f"   metadata.tables keys: {list(Base.metadata.tables.keys())}")

    test_table = Base.metadata.tables["test"]
    print(f"   Test table's schema: {test_table.schema!r}")
    print(f"   Test table's fullname: {test_table.fullname!r}")

    print("\n2. Setting metadata.schema = 'new_schema'...")
    Base.metadata.schema = "new_schema"

    print("\n3. After setting schema:")
    print(f"   metadata.schema: {Base.metadata.schema!r}")
    print(f"   metadata.tables keys: {list(Base.metadata.tables.keys())}")

    test_table = Base.metadata.tables["test"]
    print(f"   Test table's schema: {test_table.schema!r}")
    print(f"   Test table's fullname: {test_table.fullname!r}")

    print("\n" + "=" * 60)
    print("THE PROBLEM:")
    print("- metadata.schema is updated to 'new_schema'")
    print("- BUT metadata.tables still has key 'test', not 'new_schema.test'")
    print("- AND the Table object's schema is still None")
    print("- Alembic uses metadata.tables for autogenerate, so it won't")
    print("  detect the correct schema!")
    print("=" * 60)


if __name__ == "__main__":
    main()
