"""
Parser service that orchestrates product search across multiple stores.
Handles caching, rate limiting, and result aggregation.
"""
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from app.db.models import Store, Product, ParseCache
from app.parsers.base import BaseParser, ProductData, ParseError
from app.parsers.factory import parser_factory, get_parser_for_store
from app.schemas import ProductCreate, ParserStatus as ParserStatusSchema
from app.config import settings


class ParserService:
    """
    Service for managing product parsing across multiple stores.
    Handles caching, concurrent parsing, and result normalization.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.results: Dict[int, List[ProductData]] = {}  # store_id -> products
    
    async def search_all_stores(
        self,
        query: str,
        store_ids: Optional[List[int]] = None,
        force_refresh: bool = False,
    ) -> Tuple[List[ProductData], List[ParserStatusSchema]]:
        """
        Search for products across all active stores.
        
        Args:
            query: Search query string
            store_ids: Optional list of specific store IDs to search (None = all active)
            force_refresh: If True, ignore cache and re-parse everything
            
        Returns:
            Tuple of (all_products, parser_statuses)
        """
        start_time = time.time()
        
        # Get target stores
        stores = await self._get_target_stores(store_ids)
        
        if not stores:
            logger.warning(f"No active stores found for query '{query}'")
            return [], []
        
        logger.info(f"Starting search for '{query}' across {len(stores)} stores")
        
        # Initialize status tracking
        statuses = [
            ParserStatusSchema(
                store_id=store.id,
                store_name=store.name,
                status="pending",
            )
            for store in stores
        ]
        status_map = {s.store_id: s for s in statuses}
        
        # Parse each store (with rate limiting)
        tasks = []
        for i, store in enumerate(stores):
            # Add delay between requests to avoid rate limiting
            if i > 0:
                await asyncio.sleep(settings.REQUEST_DELAY_MS / 1000)
            
            task = self._parse_store_with_cache(
                store=store,
                query=query,
                force_refresh=force_refresh,
                status=status_map[store.id],
            )
            tasks.append(task)
        
        # Execute all parsing tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_products = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Store parsing failed: {result}")
                continue
            if isinstance(result, list):
                all_products.extend(result)
        
        # Save products to database
        if all_products:
            await self._save_products(all_products, query)
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Search completed for '{query}': {len(all_products)} products in {elapsed_ms:.0f}ms")
        
        return all_products, statuses
    
    async def _get_target_stores(self, store_ids: Optional[List[int]]) -> List[Store]:
        """Get list of stores to search."""
        query = select(Store).where(Store.is_active == True)
        
        if store_ids:
            query = query.where(Store.id.in_(store_ids))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _parse_store_with_cache(
        self,
        store: Store,
        query: str,
        force_refresh: bool,
        status: ParserStatusSchema,
    ) -> List[ProductData]:
        """
        Parse a single store with cache checking.
        
        Returns cached results if available and not expired,
        otherwise parses and caches new results.
        """
        status.status = "parsing"
        
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = await self._get_from_cache(store.id, query)
                if cached_data:
                    logger.debug(f"Cache hit for store {store.id}, query '{query}'")
                    status.status = "completed"
                    status.products_found = len(cached_data)
                    return cached_data
            
            # Parse fresh data
            parser = await get_parser_for_store(store)
            products = await parser.search_products(query)
            
            # Save to cache
            await self._save_to_cache(store.id, query, products)
            
            # Update status
            status.status = "completed"
            status.products_found = len(products)
            
            logger.info(f"Parsed store {store.name}: {len(products)} products")
            return products
            
        except ParseError as e:
            logger.warning(f"Parse error for store {store.name}: {e}")
            status.status = "failed"
            status.error = str(e)
            return []
            
        except Exception as e:
            logger.exception(f"Unexpected error parsing store {store.name}: {e}")
            status.status = "failed"
            status.error = f"{type(e).__name__}: {str(e)}"
            return []
    
    async def _get_from_cache(self, store_id: int, query: str) -> Optional[List[ProductData]]:
        """
        Retrieve parsed products from cache if not expired.
        """
        query_hash = BaseParser.get_query_hash(query)
        
        stmt = select(ParseCache).where(
            ParseCache.store_id == store_id,
            ParseCache.query_hash == query_hash,
            ParseCache.expires_at > datetime.utcnow(),
        )
        
        result = await self.db.execute(stmt)
        cache_entry = result.scalar_one_or_none()
        
        if not cache_entry or not cache_entry.raw_data:
            return None
        
        # Reconstruct ProductData objects from cached JSON
        products = []
        for item in cache_entry.raw_data:
            try:
                product = ProductData(
                    name=item['name'],
                    price=item['price'],
                    brand=item.get('brand'),
                    volume=item.get('volume'),
                    volume_unit=item.get('volume_unit'),
                    url=item.get('url'),
                    image_url=item.get('image_url'),
                )
                products.append(product)
            except Exception as e:
                logger.debug(f"Failed to reconstruct cached product: {e}")
                continue
        
        return products if products else None
    
    async def _save_to_cache(self, store_id: int, query: str, products: List[ProductData]):
        """
        Save parsed products to cache.
        """
        query_hash = BaseParser.get_query_hash(query)
        
        # Remove old cache entry if exists
        await self.db.execute(
            delete(ParseCache).where(
                ParseCache.store_id == store_id,
                ParseCache.query_hash == query_hash,
            )
        )
        
        # Serialize products to JSON-serializable format
        raw_data = [
            {
                'name': p.name,
                'price': p.price,
                'brand': p.brand,
                'volume': p.volume,
                'volume_unit': p.volume_unit,
                'url': p.url,
                'image_url': p.image_url,
            }
            for p in products
        ]
        
        # Create new cache entry
        cache_entry = ParseCache(
            store_id=store_id,
            query_hash=query_hash,
            query=query,
            raw_data=raw_data,
            cached_at=datetime.utcnow(),
            expires_at=BaseParser.get_cache_expiry(),
        )
        
        self.db.add(cache_entry)
        await self.db.flush()
    
    async def _save_products(self, products: List[ProductData], query: str):
        """
        Save parsed products to the database.
        """
        for product in products:
            db_product = product.to_product_create(
                store_id=product.__dict__.get('_store_id', products[0].__dict__.get('_store_id', 1)),
                query=query,
            )
            # Note: In a real implementation, we'd track store_id properly
            # This is simplified for the demo
        
        # Bulk insert would go here
        # For now, products are saved individually by the API layer
        pass
    
    async def cleanup_old_cache(self):
        """Remove expired cache entries."""
        await self.db.execute(
            delete(ParseCache).where(ParseCache.expires_at < datetime.utcnow())
        )
        await self.db.commit()
        logger.info("Cleaned up expired cache entries")


# Service factory
def get_parser_service(db_session: AsyncSession) -> ParserService:
    """Create a new parser service instance."""
    return ParserService(db_session)
