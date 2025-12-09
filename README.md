# SQLAlchemy Metadata Schema Issue with Alembic

This repository demonstrates a common issue when using SQLAlchemy's `Metadata.schema` with Alembic autogenerate, and provides solutions.

## The Problem

When you define models in one package and want to use them with a different schema in another package (e.g., for multi-tenant applications), you might try:

```python
from models import Base

# Try to set the schema for migrations
Base.metadata.schema = 'tenant_a'
```

**This doesn't work as expected!** While `metadata.schema` is updated, the individual `Table` objects and their keys in `metadata.tables` remain unchanged. Alembic uses `metadata.tables` for autogenerate, so it won't detect the correct schema.

### Before (Broken)
```
metadata.schema: 'tenant_a'
metadata.tables keys: ['test']  # No schema prefix!
Table.schema: None              # Still None!
```

### After (Fixed)
```
metadata.schema: 'tenant_a'
metadata.tables keys: ['tenant_a.test']  # Correct!
Table.schema: 'tenant_a'                  # Correct!
```

## The Solution

Clone the metadata with the desired schema using `table.to_metadata()`:

```python
def clone_metadata_with_schema(source_metadata: MetaData, schema: str) -> MetaData:
    """Create a new MetaData with all tables from source, applying the schema."""
    new_metadata = MetaData(schema=schema)
    for table in source_metadata.tables.values():
        table.to_metadata(new_metadata, schema=schema)
    return new_metadata
```

## Project Structure

```
.
├── packages/
│   ├── models/              # Shared models package (schema-agnostic)
│   │   └── src/models/
│   │       ├── base.py      # DeclarativeBase with MetaData()
│   │       └── test.py      # Example model
│   └── consumer/            # Consumer package that uses models
│       ├── alembic/
│       │   └── env.py       # Uses clone_metadata_with_schema()
│       └── alembic.ini
├── scripts/
│   ├── demonstrate_problem.py   # Shows the issue
│   └── demonstrate_solution.py  # Shows all solutions
├── docker-compose.yml       # PostgreSQL for testing
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (for PostgreSQL)

### Run the demonstration scripts (no database needed)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e packages/models
pip install -e packages/consumer

# Run the problem demonstration
python scripts/demonstrate_problem.py

# Run solutions (all or specific ones)
python scripts/demonstrate_solution.py --list    # List available solutions
python scripts/demonstrate_solution.py           # Run all solutions
python scripts/demonstrate_solution.py 4         # Run solution 4 only
```

### Run with PostgreSQL and Alembic

```bash
# Start PostgreSQL (uses port 5433 to avoid conflicts)
docker compose up -d

# Wait for PostgreSQL to be ready
docker compose ps

# Set up environment
source .venv/bin/activate
pip install -e packages/models
pip install -e packages/consumer

# Generate a migration with the correct schema
cd packages/consumer
TARGET_SCHEMA=tenant_a alembic revision --autogenerate -m "initial"

# Check that the migration includes schema='tenant_a'
cat alembic/versions/*.py

# Run the migration
TARGET_SCHEMA=tenant_a alembic upgrade head

# Clean up
cd ../..
docker compose down -v
```

## Alternative Solutions

The `demonstrate_solution.py` script shows 4 different approaches:

### 1. Update Table schemas at runtime

Mutates existing Table objects. Works but modifies the original metadata.

### 2. Set schema at model definition time

```python
class MyModel(Base):
    __tablename__ = "my_table"
    __table_args__ = {"schema": "tenant_a"}  # Set at definition
```

### 3. Use MetaData(schema=...) before defining models

```python
class Base(DeclarativeBase):
    metadata = MetaData(schema="tenant_a")  # Default schema for new tables
```

### 4. Clone metadata with new schema (recommended)

```python
def clone_metadata_with_schema(source_metadata: MetaData, schema: str) -> MetaData:
    new_metadata = MetaData(schema=schema)
    for table in source_metadata.tables.values():
        table.to_metadata(new_metadata, schema=schema)
    return new_metadata
```

This is the recommended approach because:
- Doesn't mutate the original metadata
- Multiple consumers can use different schemas simultaneously
- Clean integration with Alembic's autogenerate

## Why This Happens

When you define a model class, SQLAlchemy:
1. Creates a `Table` object with `schema=None` (unless specified)
2. Registers it in `metadata.tables` with key = `tablename` (no schema prefix)

Setting `metadata.schema` later only affects:
- The **default schema** for **new** tables created afterward
- Operations like `metadata.create_all()` when combined with `schema_translate_map`

It does **not** retroactively update:
- Existing `Table.schema` attributes
- Keys in `metadata.tables`
- What Alembic's autogenerate sees

## License

MIT
