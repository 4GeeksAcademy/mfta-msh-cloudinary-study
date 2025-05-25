from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

db = SQLAlchemy()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped["UserRole"] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
        }

    def __repr__(self):
        return self.email


class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(600), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
        }

    def __repr__(self):
        return self.name