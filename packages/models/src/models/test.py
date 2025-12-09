"""Test model."""
from uuid import uuid4, UUID

from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Test(Base):
    """Test model with id and name fields."""

    __tablename__ = "test"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
