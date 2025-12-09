"""
Alembic environment configuration with schema support.

Uses clone_metadata_with_schema() to apply a target schema to models
imported from a shared package without mutating the original metadata.
"""

# pylint: disable=no-member,wrong-import-order
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, MetaData

from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

TARGET_SCHEMA = os.environ.get("TARGET_SCHEMA", "tenant_a")


def clone_metadata_with_schema(source_metadata: MetaData, schema: str) -> MetaData:
    """
    Create a new MetaData with all tables from source, applying the schema.

    This doesn't mutate the original metadata, allowing multiple consumers
    to use different schemas simultaneously.
    """
    new_metadata = MetaData(schema=schema)
    for table in source_metadata.tables.values():
        table.to_metadata(new_metadata, schema=schema)
    return new_metadata


target_metadata = clone_metadata_with_schema(Base.metadata, TARGET_SCHEMA)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=TARGET_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=TARGET_SCHEMA,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
