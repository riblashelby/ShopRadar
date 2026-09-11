"""
Parser for Pyaterochka (Пятёрочка) online catalog.
Uses their public API when available, falls back to HTML parsing.

Note: This is a demo implementation. In production, you would need to:
1. Find the actual API endpoints used by their mobile app
2. Handle authentication tokens if required
3. Respect their robots.txt and terms of service
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from loguru import logger

from app.parsers.base import BaseParser, ProductData, ParseError
from app.config import settings


class PyaterochkaParser(BaseParser):
    """
    Parser for Пятёрочка store chain.
    
    Pyaterochka has a relatively accessible online catalog.
    This parser attempts to use their search API first, then falls back to HTML.
    
    API Discovery Notes:
    - Mobile app uses: https://5post.ru/api/ or similar endpoints
    - Web catalog: https://5ka.ru/
    - Search endpoint pattern: https://5ka.ru/api/v2/search/?query={query}
    
    To find API endpoints for other stores:
    1. Open browser DevTools (F12)
    2. Go to Network tab
    3. Visit the store's website and perform a search
    4. Look for XHR/Fetch requests containing product data
    5. Check the request/response format
    """
    
    CHAIN_NAME = "pyaterochka"
    SUPPORTED_DOMAINS = ["5ka.ru", "5post.ru"]
    
    # Known API endpoints (may change, verify before production use)
    BASE_API_URL = "https://5ka.ru/api/v2"
    SEARCH_ENDPOINT = "/search/"
    
    def __init__(self, store_id: int, catalog_url: Optional[str] = None):
        super().__init__(store_id, catalog_url)
        self.session: Optional[httpx.AsyncClient] = None
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json, text/html;q=0.9",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
        }
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session with proper configuration."""
        if self.session is None or self.session.is_closed:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=settings.REQUEST_TIMEOUT_SEC,
                follow_redirects=True,
            )
        return self.session
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.is_closed:
            await self.session.aclose()
            self.session = None
    
    async def search_products(self, query: str) -> List[ProductData]:
        """
        Search for products in Pyaterochka catalog.
        
        Strategy:
        1. Try API endpoint first (faster, structured data)
        2. Fall back to HTML parsing if API fails
        3. Apply fuzzy matching to filter relevant results
        """
        products = []
        
        # Try API first
        try:
            products = await self._search_via_api(query)
            if products:
                logger.info(f"Pyaterochka API returned {len(products)} products for '{query}'")
                return products
        except Exception as e:
            logger.warning(f"Pyaterochka API failed for '{query}': {e}")
        
        # Fallback to HTML parsing
        try:
            products = await self._search_via_html(query)
            logger.info(f"Pyaterochka HTML parsing returned {len(products)} products for '{query}'")
        except Exception as e:
            logger.error(f"Pyaterochka HTML parsing failed for '{query}': {e}")
            raise ParseError(f"Failed to parse Pyaterochka: {str(e)}")
        
        return products
    
    async def _search_via_api(self, query: str) -> List[ProductData]:
        """
        Search using Pyaterochka's API endpoint.
        
        Note: API structure may change. Verify response format before production use.
        """
        session = await self._get_session()
        
        # Construct API URL
        api_url = f"{self.BASE_API_URL}{self.SEARCH_ENDPOINT}"
        params = {
            "query": query,
            "limit": 50,  # Limit results for performance
        }
        
        response = await session.get(api_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        products = []
        
        # Parse API response structure
        # Adjust based on actual API response format
        items = data.get("results", []) or data.get("data", []) or []
        
        for item in items:
            try:
                product = self._parse_api_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Failed to parse API item: {e}")
                continue
        
        return products
    
    async def _search_via_html(self, query: str) -> List[ProductData]:
        """
        Search by parsing HTML from the catalog page.
        Used as fallback when API is unavailable.
        """
        session = await self._get_session()
        
        # Construct search URL
        search_url = f"https://5ka.ru/catalog?q={query}"
        
        response = await session.get(search_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        products = []
        
        # Find product cards in HTML
        # Adjust selectors based on actual HTML structure
        product_cards = soup.select('.catalog-item, .product-card, [data-product]')
        
        for card in product_cards[:30]:  # Limit to 30 results
            try:
                product = self._parse_html_card(card, query, search_url)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Failed to parse HTML card: {e}")
                continue
        
        return products
    
    def _parse_api_item(self, item: Dict[str, Any], query: str) -> Optional[ProductData]:
        """Parse a single product from API response."""
        try:
            # Extract fields from API response
            # Adjust field names based on actual API structure
            name = item.get("name", "") or item.get("title", "")
            if not name:
                return None
            
            # Check fuzzy match
            if not self._fuzzy_match(name, query):
                return None
            
            # Price
            price_data = item.get("price", {}) or {}
            price = float(price_data.get("current", 0) or price_data.get("value", 0) or 0)
            if price <= 0:
                price = float(item.get("price", 0) or 0)
            
            if price <= 0:
                return None
            
            # Volume
            volume_str = item.get("volume", "") or item.get("weight", "") or ""
            volume, volume_unit = self._extract_volume(volume_str)
            
            # If no volume in dedicated field, try extracting from name
            if volume is None:
                volume, volume_unit = self._extract_volume(name)
            
            # Brand
            brand = item.get("brand", "") or item.get("manufacturer", "")
            
            # URL
            url = item.get("url", "") or item.get("link", "")
            if url and not url.startswith("http"):
                url = f"https://5ka.ru{url}"
            
            # Image
            image_url = item.get("image", "") or item.get("img", "") or item.get("picture", "")
            
            return ProductData(
                name=name.strip(),
                price=price,
                brand=brand.strip() if brand else None,
                volume=volume,
                volume_unit=volume_unit,
                url=url,
                image_url=image_url,
            )
        except Exception as e:
            logger.debug(f"Error parsing API item: {e}")
            return None
    
    def _parse_html_card(self, card, query: str, base_url: str) -> Optional[ProductData]:
        """Parse a single product from HTML card element."""
        try:
            # Extract name
            name_elem = card.select_one('.product-name, .item-title, h3, .title')
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)
            
            # Check fuzzy match
            if not self._fuzzy_match(name, query):
                return None
            
            # Extract price
            price_elem = card.select_one('.price-current, .price-value, .cost, [class*="price"]')
            if not price_elem:
                return None
            price_text = price_elem.get_text(strip=True)
            price = self._clean_price(price_text)
            if not price or price <= 0:
                return None
            
            # Extract volume from name or description
            volume_elem = card.select_one('.volume, .weight, .size, .unit')
            volume = None
            volume_unit = None
            
            if volume_elem:
                volume_text = volume_elem.get_text(strip=True)
                volume, volume_unit = self._extract_volume(volume_text)
            
            if volume is None:
                volume, volume_unit = self._extract_volume(name)
            
            # Extract URL
            link_elem = card.select_one('a[href]')
            url = None
            if link_elem:
                href = link_elem.get('href', '')
                if href:
                    url = href if href.startswith('http') else f"https://5ka.ru{href}"
            
            # Extract image
            img_elem = card.select_one('img[src]')
            image_url = None
            if img_elem:
                src = img_elem.get('src', '') or img_elem.get('data-src', '')
                if src:
                    image_url = src if src.startswith('http') else f"https://5ka.ru{src}"
            
            # Extract brand (if available)
            brand_elem = card.select_one('.brand, .manufacturer')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            return ProductData(
                name=name,
                price=price,
                brand=brand,
                volume=volume,
                volume_unit=volume_unit,
                url=url,
                image_url=image_url,
            )
        except Exception as e:
            logger.debug(f"Error parsing HTML card: {e}")
            return None
    
    async def get_store_info(self) -> Dict[str, Any]:
        """Get additional store information."""
        info = await super().get_store_info()
        info["api_available"] = True
        info["parser_version"] = "1.0"
        return info
