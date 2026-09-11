"""
Pydantic schemas for request/response validation.
Used for API input/output serialization.
"""
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StoreChainEnum(str, Enum):
    """Store chain identifiers matching the database enum."""
    magnit = "magnit"
    pyaterochka = "pyaterochka"
    chizhik = "chizhik"
    kb = "kb"
    custom = "custom"


# ============== STORE SCHEMAS ==============

class StoreBase(BaseModel):
    """Base schema for store data."""
    name: str = Field(..., min_length=1, max_length=255, description="Store name, e.g., 'Магнит на ул. Ленина 5'")
    chain: StoreChainEnum = Field(default=StoreChainEnum.custom, description="Store chain identifier")
    address: Optional[str] = Field(None, max_length=500, description="Physical address")
    catalog_url: Optional[HttpUrl] = Field(None, description="Base URL for online catalog")
    is_active: bool = Field(True, description="Whether this store is enabled for search")


class StoreCreate(StoreBase):
    """Schema for creating a new store."""
    pass


class StoreUpdate(BaseModel):
    """Schema for updating an existing store (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    chain: Optional[StoreChainEnum] = None
    address: Optional[str] = Field(None, max_length=500)
    catalog_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Schema for store response with additional metadata."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StoreWithProductCount(StoreResponse):
    """Store response with product count for UI display."""
    product_count: int = 0


# ============== PRODUCT SCHEMAS ==============

class ProductBase(BaseModel):
    """Base schema for product data."""
    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    brand: Optional[str] = Field(None, max_length=255, description="Brand name if available")
    price: float = Field(..., gt=0, description="Price in rubles")
    volume: Optional[float] = Field(None, gt=0, description="Volume/weight value")
    volume_unit: Optional[str] = Field(None, description="Unit: ml, g, l, kg, pcs")
    unit_price: Optional[float] = Field(None, ge=0, description="Price per liter/kg for comparison")
    url: Optional[HttpUrl] = Field(None, description="Direct link to product page")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")


class ProductCreate(ProductBase):
    """Schema for creating a product (internal use)."""
    store_id: int
    query: str = Field(..., min_length=1, max_length=255)


class ProductResponse(ProductBase):
    """Schema for product response with store information."""
    id: int
    store_id: int
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    query: str
    parsed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductSearchResult(ProductResponse):
    """Extended product response for search results with ranking info."""
    is_best_offer: bool = Field(False, description="Whether this is the best priced option")
    rank: int = Field(1, description="Ranking position by unit price")


# ============== SEARCH SCHEMAS ==============

class SearchRequest(BaseModel):
    """Schema for product search request."""
    query: str = Field(..., min_length=1, max_length=255, description="Search query, e.g., 'кола', 'молоко'")
    force_refresh: bool = Field(False, description="Force re-parsing even if cached")
    store_ids: Optional[List[int]] = Field(None, description="Specific stores to search (None = all active)")


class SearchResult(BaseModel):
    """Schema for search results response."""
    query: str
    total_results: int
    stores_searched: int
    stores_failed: int
    products: List[ProductSearchResult]
    search_time_ms: float
    cached: bool = False


class SearchHistoryItem(BaseModel):
    """Schema for search history item."""
    id: int
    query: str
    results_count: int
    searched_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============== SHOPPING LIST SCHEMAS ==============

class ShoppingListItem(BaseModel):
    """Single item in a shopping list."""
    name: str
    quantity: int = Field(1, ge=1)
    best_price: Optional[float] = None
    store_id: Optional[int] = None
    store_name: Optional[str] = None


class ShoppingListCreate(BaseModel):
    """Schema for creating a shopping list."""
    name: str = Field(..., min_length=1, max_length=255)
    items: List[ShoppingListItem] = Field(default_factory=list)


class ShoppingListResponse(BaseModel):
    """Schema for shopping list response."""
    id: int
    name: str
    items: List[ShoppingListItem]
    total_cost: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============== FAVORITE SCHEMAS ==============

class FavoriteItemCreate(BaseModel):
    """Schema for adding a favorite item."""
    product_name: str
    best_price: Optional[float] = None
    best_store_id: Optional[int] = None


class FavoriteItemResponse(BaseModel):
    """Schema for favorite item response."""
    id: int
    product_name: str
    best_price: Optional[float]
    best_store_id: Optional[int]
    best_store_name: Optional[str] = None
    added_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============== PARSER STATUS SCHEMAS ==============

class ParserStatus(BaseModel):
    """Status of a parser operation."""
    store_id: int
    store_name: str
    status: str  # "pending", "parsing", "completed", "failed"
    error: Optional[str] = None
    products_found: int = 0


class ParseProgress(BaseModel):
    """Progress of multi-store parsing operation."""
    total_stores: int
    completed: int
    failed: int
    pending: int
    statuses: List[ParserStatus]
    overall_progress: float  # 0.0 to 1.0
