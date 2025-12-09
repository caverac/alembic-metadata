"""Base model configuration."""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models. Schema is intentionally NOT set here."""

    metadata = MetaData()
