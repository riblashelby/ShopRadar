"""
Base parser interface and utilities for product parsing.
All store-specific parsers must implement the BaseParser interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import re

from app.schemas import ProductCreate
from app.config import settings


class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


class ProductData:
    """
    Internal data class for parsed product information.
    Used before validation and database insertion.
    """
    def __init__(
        self,
        name: str,
        price: float,
        brand: Optional[str] = None,
        volume: Optional[float] = None,
        volume_unit: Optional[str] = None,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.name = name
        self.price = price
        self.brand = brand
        self.volume = volume
        self.volume_unit = volume_unit
        self.url = url
        self.image_url = image_url
        self.unit_price = self._calculate_unit_price()
    
    def _calculate_unit_price(self) -> Optional[float]:
        """
        Calculate price per liter or per kg for comparison.
        Returns None if volume information is not available.
        """
        if self.volume is None or self.volume_unit is None:
            return None
        
        # Normalize to liters or kilograms
        volume_in_base_unit = self._normalize_volume()
        if volume_in_base_unit is None or volume_in_base_unit == 0:
            return None
        
        return round(self.price / volume_in_base_unit, 2)
    
    def _normalize_volume(self) -> Optional[float]:
        """
        Normalize volume to base units (liters for liquids, kg for weight).
        """
        if self.volume_unit is None:
            return None
        
        unit_lower = self.volume_unit.lower()
        
        # Volume conversions to liters
        if unit_lower in ['ml', 'мл']:
            return self.volume / 1000
        elif unit_lower in ['l', 'л', 'liter', 'литр']:
            return self.volume
        # Weight conversions to kg
        elif unit_lower in ['g', 'г', 'gram', 'грамм']:
            return self.volume / 1000
        elif unit_lower in ['kg', 'кг', 'kilogram', 'килограмм']:
            return self.volume
        # Pieces - no normalization needed
        elif unit_lower in ['pcs', 'шт', 'piece', 'штука']:
            return self.volume
        
        return None
    
    def to_product_create(self, store_id: int, query: str) -> ProductCreate:
        """Convert to Pydantic schema for database insertion."""
        return ProductCreate(
            name=self.name,
            brand=self.brand,
            price=self.price,
            volume=self.volume,
            volume_unit=self.volume_unit,
            unit_price=self.unit_price,
            url=self.url,
            image_url=self.image_url,
            store_id=store_id,
            query=query,
        )


class BaseParser(ABC):
    """
    Abstract base class for all store parsers.
    Each store chain (Магнит, Пятёрочка, etc.) must implement this interface.
    """
    
    # Class-level configuration
    CHAIN_NAME: str = "base"  # Identifier matching StoreChain enum
    SUPPORTED_DOMAINS: List[str] = []  # URL domains this parser handles
    
    def __init__(self, store_id: int, catalog_url: Optional[str] = None):
        """
        Initialize parser for a specific store.
        
        Args:
            store_id: Database ID of the store
            catalog_url: Base URL for the store's online catalog
        """
        self.store_id = store_id
        self.catalog_url = catalog_url
        self.session = None  # HTTP session to be set by caller
    
    @abstractmethod
    async def search_products(self, query: str) -> List[ProductData]:
        """
        Search for products matching the query in this store's catalog.
        
        Args:
            query: Search query (e.g., "кола", "молоко")
            
        Returns:
            List of ProductData objects with parsed product information
            
        Raises:
            ParseError: If parsing fails due to network issues, 
                       unexpected HTML structure, etc.
        """
        pass
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get additional store information (optional).
        Can be used to verify store availability, get metadata, etc.
        
        Returns:
            Dictionary with store metadata
        """
        return {
            "store_id": self.store_id,
            "chain": self.CHAIN_NAME,
            "catalog_url": self.catalog_url,
        }
    
    def _fuzzy_match(self, text: str, query: str, threshold: float = 0.5) -> bool:
        """
        Perform fuzzy matching between text and query.
        Simple implementation based on token overlap.
        
        Args:
            text: Text to search in
            query: Search query
            threshold: Minimum similarity score (0-1)
            
        Returns:
            True if text matches query with sufficient similarity
        """
        if not text or not query:
            return False
        
        # Normalize both strings
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Direct substring match
        if query_lower in text_lower:
            return True
        
        # Token-based matching
        text_tokens = set(re.findall(r'\w+', text_lower))
        query_tokens = set(re.findall(r'\w+', query_lower))
        
        if not query_tokens:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(text_tokens & query_tokens)
        union = len(text_tokens | query_tokens)
        
        if union == 0:
            return False
        
        similarity = intersection / union
        return similarity >= threshold
    
    def _extract_volume(self, text: str) -> tuple[Optional[float], Optional[str]]:
        """
        Extract volume/weight information from product text.
        
        Args:
            text: Product name or description text
            
        Returns:
            Tuple of (volume_value, volume_unit) or (None, None) if not found
        """
        if not text:
            return None, None
        
        # Common patterns for volume/weight
        patterns = [
            # Milliliters: 330 мл, 500ml, 0.5 л
            (r'(\d+[.,]?\d*)\s*(мл|ml)', 'ml'),
            (r'(\d+[.,]?\d*)\s*(л|l|литр)', 'l'),
            # Grams: 100 г, 500gram
            (r'(\d+[.,]?\d*)\s*(г|g|грамм)', 'g'),
            (r'(\d+[.,]?\d*)\s*(кг|kg)', 'kg'),
            # Pieces: 1 шт, 2 pieces
            (r'(\d+)\s*(шт|pcs|piece)', 'pcs'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1).replace(',', '.')
                    value = float(value_str)
                    return value, unit
                except (ValueError, IndexError):
                    continue
        
        return None, None
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """
        Extract numeric price from text.
        
        Args:
            price_text: Text containing price (e.g., "99.99 ₽", "100 руб.")
            
        Returns:
            Float price value or None if not found
        """
        if not price_text:
            return None
        
        # Remove currency symbols and extract number
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle different decimal separators
        cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def get_query_hash(query: str) -> str:
        """Generate MD5 hash of query for cache lookup."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    @staticmethod
    def get_cache_expiry() -> datetime:
        """Calculate cache expiry time based on settings."""
        return datetime.utcnow() + timedelta(hours=settings.CACHE_TTL_HOURS)
