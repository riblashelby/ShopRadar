"""
Database models for CheapCart application.
Uses SQLAlchemy ORM with async support.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class StoreChain(enum.Enum):
    """Supported store chains with their identifiers."""
    MAGNIT = "magnit"
    PYATEROCHKA = "pyaterochka"
    CHIZHIK = "chizhik"
    KB = "kb"  # Krasnoe & Beloe
    CUSTOM = "custom"


class Store(Base):
    """
    Represents a specific store location (торговая точка).
    Each store belongs to a chain and has its own address and catalog URL.
    """
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Магнит на ул. Ленина 5"
    chain = Column(Enum(StoreChain), nullable=False, default=StoreChain.CUSTOM)
    address = Column(String(500), nullable=True)
    lat = Column(Float, nullable=True)  # Latitude for future map features
    lng = Column(Float, nullable=True)  # Longitude
    catalog_url = Column(String(1000), nullable=True)  # Base URL for this store's catalog
    is_active = Column(Boolean, default=True, nullable=False)  # Enable/disable for search
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    favorite_items = relationship("FavoriteItem", back_populates="store", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Store(id={self.id}, name='{self.name}', chain={self.chain.value})>"


class Product(Base):
    """
    Cached product data from parsing results.
    Stores normalized data for comparison across stores.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    
    # Product identification
    name = Column(String(500), nullable=False)  # Full product name from store
    brand = Column(String(255), nullable=True)  # Extracted brand if available
    
    # Pricing
    price = Column(Float, nullable=False)  # Absolute price in rubles
    volume = Column(Float, nullable=True)  # Volume/weight value
    volume_unit = Column(String(20), nullable=True)  # ml, g, l, kg, pcs
    unit_price = Column(Float, nullable=True)  # Price per liter/kg for comparison
    
    # Metadata
    url = Column(String(1000), nullable=True)  # Direct link to product page
    image_url = Column(String(1000), nullable=True)
    query = Column(String(255), nullable=False, index=True)  # Search query that found this
    parsed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    store = relationship("Store", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, store_id={self.store_id})>"


class SearchHistory(Base):
    """
    History of user search queries for analytics and quick access.
    """
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(255), nullable=False, index=True)
    results_count = Column(Integer, default=0)
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SearchHistory(query='{self.query}', count={self.results_count})>"


class FavoriteItem(Base):
    """
    User's favorite/saved items with best known price tracking.
    """
    __tablename__ = "favorite_items"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(500), nullable=False)
    best_price = Column(Float, nullable=True)
    best_store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    store = relationship("Store", back_populates="favorite_items")
    
    def __repr__(self):
        return f"<FavoriteItem(name='{self.product_name}', best_price={self.best_price})>"


class ShoppingList(Base):
    """
    Shopping list with multiple items.
    Items stored as JSON for simplicity in self-hosted scenario.
    """
    __tablename__ = "shopping_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    items = Column(JSON, default=list)  # List of {name, quantity, best_price, store_id}
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ShoppingList(name='{self.name}', items={len(self.items)})>"


class ParseCache(Base):
    """
    Cache table for storing raw parse results to avoid re-parsing.
    Keyed by store_id + search_query hash.
    """
    __tablename__ = "parse_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)  # MD5 of query
    query = Column(String(255), nullable=False)
    raw_data = Column(JSON, nullable=True)  # Raw parsed products as JSON
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<ParseCache(store_id={self.store_id}, query='{self.query}')>"
