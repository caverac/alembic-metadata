"""
Demonstrates solutions for the SQLAlchemy Metadata.schema issue with Alembic.

Solutions:
1. Update schema on existing Table objects (works for existing metadata)
2. Use __table_args__ with schema in model definition
3. Factory function that generates models with the desired schema
4. Clone metadata with new schema

Usage:
    python demonstrate_solution.py           # Run all solutions
    python demonstrate_solution.py 1         # Run solution 1 only
    python demonstrate_solution.py 1 2 4     # Run solutions 1, 2, and 4
    python demonstrate_solution.py --list    # List available solutions
"""

import argparse
import sys
from uuid import uuid4, UUID

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ============================================================================
# SOLUTION 1: Update schema on existing Table objects
# ============================================================================


class Base1(DeclarativeBase):
    """Models without schema - defined in a shared package."""

    metadata = MetaData()


class Test1(Base1):
    """Test model without schema."""

    __tablename__ = "test"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)


def update_table_schemas(metadata: MetaData, schema: str) -> None:
    """
    Update the schema on all Table objects in the metadata.

    This is the key insight: you need to update the Table objects themselves,
    not just the metadata.schema attribute.
    """
    tables_to_update = list(metadata.tables.values())

    for table in tables_to_update:
        metadata.remove(table)
        table.schema = schema
        # pylint: disable=protected-access
        metadata._add_table(table.name, schema, table)


def demonstrate_solution_1() -> None:
    """Demonstrate updating Table objects to set schema."""
    print("\n" + "=" * 60)
    print("SOLUTION 1: Update schema on existing Table objects")
    print("=" * 60)
    print("\nUse case: You have models defined elsewhere without a schema,")
    print("and need to add a schema at runtime (e.g., in Alembic env.py).")

    print("\n1. Initial state:")
    print(f"   metadata.tables keys: {list(Base1.metadata.tables.keys())}")
    test_table = Base1.metadata.tables["test"]
    print(f"   Test table schema: {test_table.schema!r}")

    print("\n2. Calling update_table_schemas(metadata, 'tenant_a')...")
    update_table_schemas(Base1.metadata, "tenant_a")

    print("\n3. After update:")
    print(f"   metadata.tables keys: {list(Base1.metadata.tables.keys())}")
    test_table = Base1.metadata.tables["tenant_a.test"]
    print(f"   Test table schema: {test_table.schema!r}")
    print(f"   Test table fullname: {test_table.fullname!r}")


# ============================================================================
# SOLUTION 2: Use __table_args__ to set schema at definition time
# ============================================================================


class Base2(DeclarativeBase):
    """Models defined with schema in __table_args__."""

    metadata = MetaData()


class Test2(Base2):
    """Test model with schema set in __table_args__."""

    __tablename__ = "test"
    __table_args__ = {"schema": "tenant_b"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)


def demonstrate_solution_2() -> None:
    """Demonstrate using __table_args__ to set schema."""
    print("\n" + "=" * 60)
    print("SOLUTION 2: Use __table_args__ at definition time")
    print("=" * 60)
    print("\nUse case: You know the schema upfront and can hardcode it")
    print("in your model definitions.")

    print("\n1. Tables defined with __table_args__ = {'schema': 'tenant_b'}:")
    print(f"   metadata.tables keys: {list(Base2.metadata.tables.keys())}")
    test_table = Base2.metadata.tables["tenant_b.test"]
    print(f"   Test table schema: {test_table.schema!r}")
    print(f"   Test table fullname: {test_table.fullname!r}")


# ============================================================================
# SOLUTION 3: Factory function for dynamic schema
# ============================================================================


def create_models_with_schema(schema: str) -> tuple:
    """
    Factory function that creates model classes with the specified schema.

    This is flexible when you need to define models in one package
    but use them with different schemas in different consumers.
    """

    class DynamicBase(DeclarativeBase):
        """Dynamic base with specified schema."""

        metadata = MetaData(schema=schema)

    class DynamicTest(DynamicBase):
        """Dynamic Test model with specified schema."""

        __tablename__ = "test"

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        name: Mapped[str] = mapped_column(nullable=False)

    return DynamicBase, DynamicTest


def demonstrate_solution_3() -> None:
    """Demonstrate factory function for dynamic schema."""
    print("\n" + "=" * 60)
    print("SOLUTION 3: Factory function with MetaData(schema=...)")
    print("=" * 60)
    print("\nUse case: You need different schemas for different deployments,")
    print("and can generate models dynamically at import time.")

    print("\n1. Creating models with schema='tenant_c'...")
    base, _ = create_models_with_schema("tenant_c")

    print("\n2. Result:")
    print(f"   metadata.schema: {base.metadata.schema!r}")
    print(f"   metadata.tables keys: {list(base.metadata.tables.keys())}")
    test_table = base.metadata.tables["tenant_c.test"]
    print(f"   Test table schema: {test_table.schema!r}")
    print(f"   Test table fullname: {test_table.fullname!r}")


# ============================================================================
# SOLUTION 4: Clone metadata with new schema
# ============================================================================


class Base4(DeclarativeBase):
    """Original models without schema - defined in a shared package."""

    metadata = MetaData()


class Test4(Base4):
    """Test model for solution 4."""

    __tablename__ = "test"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)


class AnotherModel4(Base4):
    """Another model for solution 4."""

    __tablename__ = "another"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    value: Mapped[int] = mapped_column(nullable=False)


def clone_metadata_with_schema(source_metadata: MetaData, schema: str) -> MetaData:
    """
    Create a new MetaData instance with all tables from source.

    Applies the specified schema to each table. This is the cleanest
    approach for Alembic because:
    - It doesn't mutate the original metadata
    - The new metadata has correct table keys from the start
    - Multiple consumers can use different schemas simultaneously
    """
    new_metadata = MetaData(schema=schema)

    for table in source_metadata.tables.values():
        table.to_metadata(new_metadata, schema=schema)

    return new_metadata


def demonstrate_solution_4() -> None:
    """Demonstrate cloning metadata with a new schema."""
    print("\n" + "=" * 60)
    print("SOLUTION 4: Clone metadata with new schema")
    print("=" * 60)
    print("\nUse case: You import models from a shared package and need to")
    print("apply a schema without modifying the original metadata.")

    print("\n1. Original metadata (from shared models package):")
    print(f"   metadata.schema: {Base4.metadata.schema!r}")
    print(f"   metadata.tables keys: {list(Base4.metadata.tables.keys())}")

    print("\n2. Cloning metadata with schema='tenant_d'...")
    cloned = clone_metadata_with_schema(Base4.metadata, "tenant_d")

    print("\n3. Cloned metadata:")
    print(f"   metadata.schema: {cloned.schema!r}")
    print(f"   metadata.tables keys: {list(cloned.tables.keys())}")

    for key, table in cloned.tables.items():
        print(f"   - {key}: schema={table.schema!r}, fullname={table.fullname!r}")

    print("\n4. Original metadata is UNCHANGED:")
    print(f"   metadata.schema: {Base4.metadata.schema!r}")
    print(f"   metadata.tables keys: {list(Base4.metadata.tables.keys())}")

    print("\n" + "-" * 60)
    print("ALEMBIC env.py EXAMPLE:")
    print("-" * 60)
    example = """
    # In your Alembic env.py:

    import os
    from models import Base  # Import from shared package

    TARGET_SCHEMA = os.environ.get("TARGET_SCHEMA", "tenant_a")

    def clone_metadata_with_schema(source_metadata, schema):
        new_metadata = MetaData(schema=schema)
        for table in source_metadata.tables.values():
            table.to_metadata(new_metadata, schema=schema)
        return new_metadata

    # Create a NEW metadata with the target schema
    target_metadata = clone_metadata_with_schema(Base.metadata, TARGET_SCHEMA)

    # Use this in your migration context
    def run_migrations_online():
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,  # Use cloned metadata!
                include_schemas=True,
                version_table_schema=TARGET_SCHEMA,
            )
            with context.begin_transaction():
                context.run_migrations()
    """
    print(example)


# ============================================================================
# CLI
# ============================================================================

SOLUTIONS = {
    "1": ("Update existing Table objects", demonstrate_solution_1),
    "2": ("Use __table_args__ at definition", demonstrate_solution_2),
    "3": ("Factory function with dynamic schema", demonstrate_solution_3),
    "4": ("Clone metadata", demonstrate_solution_4),
}


def list_solutions() -> None:
    """List all available solutions."""
    print("\nAvailable solutions:")
    print("-" * 50)
    for num, (desc, _) in SOLUTIONS.items():
        print(f"  {num}. {desc}")
    print("\nUsage:")
    print("  python demonstrate_solution.py           # Run all")
    print("  python demonstrate_solution.py 1 4       # Run specific ones")
    print("  python demonstrate_solution.py --list    # Show this list")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demonstrate solutions for SQLAlchemy Metadata schema issue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              Run all solutions
  %(prog)s 1            Run solution 1 only
  %(prog)s 1 2 4        Run solutions 1, 2, and 4
  %(prog)s --list       List available solutions
        """,
    )
    parser.add_argument(
        "solutions",
        nargs="*",
        choices=["1", "2", "3", "4"],
        metavar="N",
        help="Solution number(s) to run (1-4). Omit to run all.",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        dest="list_only",
        help="List available solutions and exit",
    )

    args = parser.parse_args()

    if args.list_only:
        list_solutions()
        sys.exit(0)

    to_run = args.solutions if args.solutions else list(SOLUTIONS.keys())

    print("=" * 60)
    print("SQLAlchemy Metadata Schema Solutions")
    print("=" * 60)

    for num in to_run:
        if num in SOLUTIONS:
            _, func = SOLUTIONS[num]
            func()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
