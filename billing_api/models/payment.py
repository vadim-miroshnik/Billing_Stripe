import enum
import uuid

from sqlalchemy import DECIMAL, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from db.postgres import Base


class Currency(enum.Enum):
    RUB = (1,)
    USD = (2,)
    EUR = 3


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = {"schema": "users"}
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    product_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), nullable=False)
    description = Column(String, unique=False, nullable=True)
    payment_intent_id = Column(String, unique=False, nullable=True)
    amount = Column(DECIMAL(10, 2))
    currency = Column("currency", Enum(Currency, name="currency_enum", create_type=False))
    pay_date = Column(DateTime(timezone=True), nullable=True)
