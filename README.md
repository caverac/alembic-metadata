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

You need to update the `schema` attribute on each `Table` object and re-register it with the metadata:

```python
def update_metadata_schema(metadata: MetaData, schema: str) -> None:
    """Update schema on all Table objects in metadata."""
    tables = list(metadata.tables.values())

    for table in tables:
        if table.schema == schema:
            continue

        # Remove from metadata's registry
        metadata.remove(table)

        # Update the table's schema
        table.schema = schema

        # Re-register (updates the key in metadata.tables)
        metadata._add_table(table.name, schema, table)

    metadata.schema = schema
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
│       │   ├── env.py       # Broken: just sets metadata.schema
│       │   └── env_fixed.py # Fixed: updates Table objects
│       └── alembic.ini
├── scripts/
│   ├── demonstrate_problem.py   # Shows the issue
│   └── demonstrate_solution.py  # Shows all solutions
├── docker-compose.yml       # PostgreSQL for testing
└── README.md
```

## Quick Start

```bash
# Run the demonstration scripts
./scripts/run_demo.sh

# Or run with PostgreSQL and Alembic
./scripts/run_alembic_demo.sh
```

## Alternative Solutions

### 1. Update Table schemas at runtime (recommended for your case)

Use the `update_metadata_schema()` function in your Alembic `env.py`. This works when you can't modify the model definitions.

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

### 4. Factory function for dynamic schemas

```python
def create_models_with_schema(schema: str):
    class DynamicBase(DeclarativeBase):
        metadata = MetaData(schema=schema)

    class MyModel(DynamicBase):
        __tablename__ = "my_table"
        # ... columns

    return DynamicBase, MyModel
```

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
