from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

db = SQLAlchemy()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped["UserRole"] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    # Relevant for this Study Project ##############################################################################################
    picture_url: Mapped[str] = mapped_column(String(500), nullable=True) # Image URL for the user profile picture
    picture_public_id: Mapped[str] = mapped_column(String(200), nullable=True) # Useful for deleting the image from Cloudinary
    ################################################################################################################################

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "picture_url": self.picture_url
        }

    def __repr__(self):
        return self.email


class Product(db.Model):
    __tablename__ = 'product'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(600), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)

    images: Mapped[list["ProductImage"]] = db.relationship(back_populates="product", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "images": [image.serialize() for image in self.images]
        }

    def __repr__(self):
        return self.name
    

class ProductImage(db.Model):
    __tablename__ = 'product_image'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(db.ForeignKey('product.id'), nullable=False)
    # Relevant for this Study Project ##############################################################################################
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    public_id: Mapped[str] = mapped_column(String(200), nullable=False)
    ################################################################################################################################

    product: Mapped["Product"] = db.relationship(back_populates="images")

    def serialize(self):
        return {
            "id": self.id,
            "url": self.url,
        }
    
    def __repr__(self):
        return self.url