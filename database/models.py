from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    short_description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    file_id = Column(String(200), nullable=True)  # Telegram file_id for the product file
    preview_image_id = Column(String(200), nullable=True)  # Telegram file_id for preview image
    available = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    purchases = relationship("Purchase", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, title={self.title}, price={self.price})>"

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    purchase_date = Column(DateTime, default=datetime.utcnow)
    purchase_price = Column(Float, nullable=False)  # Price at time of purchase
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"