"""
Product search endpoints.
Main functionality for searching products across stores.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import time

from app.db.database import get_db
from app.db.models import Store, Product, SearchHistory
from app.schemas import (
    SearchRequest,
    SearchResult,
    ProductSearchResult,
    SearchHistoryItem,
    ParseProgress,
)
from app.services.parser_service import get_parser_service
from loguru import logger

router = APIRouter()


@router.post("", response_model=SearchResult)
async def search_products(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for products across all active stores.
    
    - **query**: Search query (e.g., "кола", "молоко")
    - **force_refresh**: Force re-parsing even if results are cached
    - **store_ids**: Optional list of specific store IDs to search
    
    Returns products sorted by unit price (price per liter/kg).
    The best offer is highlighted.
    """
    start_time = time.time()
    
    # Get parser service
    parser_service = get_parser_service(db)
    
    # Search across stores
    products_data, statuses = await parser_service.search_all_stores(
        query=request.query,
        store_ids=request.store_ids,
        force_refresh=request.force_refresh,
    )
    
    # Calculate statistics
    stores_searched = len([s for s in statuses if s.status == "completed"])
    stores_failed = len([s for s in statuses if s.status == "failed"])
    
    # Convert to response format and sort by unit price
    product_responses = []
    
    for prod in products_data:
        # Get store info
        store_result = await db.execute(
            select(Store).where(Store.id == prod.__dict__.get('_store_id', 1))
        )
        store = store_result.scalar_one_or_none()
        
        if store:
            product_responses.append(ProductSearchResult(
                id=0,  # Will be assigned after save
                store_id=store.id,
                store_name=store.name,
                store_address=store.address,
                name=prod.name,
                brand=prod.brand,
                price=prod.price,
                volume=prod.volume,
                volume_unit=prod.volume_unit,
                unit_price=prod.unit_price,
                url=prod.url,
                image_url=prod.image_url,
                query=request.query,
                parsed_at=func.now(),
            ))
    
    # Sort by unit price (products without unit_price go to the end)
    product_responses.sort(
        key=lambda p: (p.unit_price is None, p.unit_price or float('inf'))
    )
    
    # Mark best offer
    if product_responses:
        product_responses[0].is_best_offer = True
    
    # Add rank
    for i, prod in enumerate(product_responses):
        prod.rank = i + 1
    
    # Save search history
    history_entry = SearchHistory(
        query=request.query,
        results_count=len(product_responses),
    )
    db.add(history_entry)
    await db.commit()
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    return SearchResult(
        query=request.query,
        total_results=len(product_responses),
        stores_searched=stores_searched,
        stores_failed=stores_failed,
        products=product_responses[:50],  # Limit to 50 results
        search_time_ms=elapsed_ms,
        cached=not request.force_refresh,
    )


@router.get("/history", response_model=List[SearchHistoryItem])
async def get_search_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent search history.
    """
    result = await db.execute(
        select(SearchHistory)
        .order_by(SearchHistory.searched_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/progress")
async def get_parse_progress(
    db: AsyncSession = Depends(get_db),
):
    """
    Get current parsing progress (for long-running searches).
    
    Note: This is a simplified implementation.
    For production, use WebSocket or server-sent events.
    """
    # This would need state management for real-time progress
    # Returning placeholder
    return ParseProgress(
        total_stores=0,
        completed=0,
        failed=0,
        pending=0,
        statuses=[],
        overall_progress=0.0,
    )
