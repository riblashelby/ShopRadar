"""
Store management endpoints.
CRUD operations for store locations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db.database import get_db
from app.db.models import Store, StoreChain, Product
from app.schemas import StoreCreate, StoreUpdate, StoreResponse, StoreWithProductCount
from loguru import logger

router = APIRouter()


@router.get("", response_model=List[StoreWithProductCount])
async def list_stores(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all stores with product counts.
    
    - **include_inactive**: If true, include disabled stores
    """
    query = select(Store)
    
    if not include_inactive:
        query = query.where(Store.is_active == True)
    
    result = await db.execute(query.order_by(Store.chain, Store.name))
    stores = list(result.scalars().all())
    
    # Get product counts for each store
    store_ids = [s.id for s in stores]
    if store_ids:
        count_query = select(
            Product.store_id,
            func.count(Product.id).label('count')
        ).where(
            Product.store_id.in_(store_ids)
        ).group_by(Product.store_id)
        
        count_result = await db.execute(count_query)
        product_counts = {row.store_id: row.count for row in count_result.all()}
    else:
        product_counts = {}
    
    # Add product counts to responses
    response = []
    for store in stores:
        store_dict = StoreWithProductCount.model_validate(store)
        store_dict.product_count = product_counts.get(store.id, 0)
        response.append(store_dict)
    
    return response


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific store by ID.
    """
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with id {store_id} not found",
        )
    
    return store


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    store_data: StoreCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new store location.
    
    - **name**: Store name (e.g., "Магнит на ул. Ленина 5")
    - **chain**: Store chain (magnit, pyaterochka, chizhik, kb, custom)
    - **address**: Physical address
    - **catalog_url**: Base URL for online catalog
    - **is_active**: Whether this store is enabled for search
    """
    # Convert enum value to StoreChain
    chain_enum = StoreChain(store_data.chain.value)
    
    store = Store(
        name=store_data.name,
        chain=chain_enum,
        address=store_data.address,
        catalog_url=str(store_data.catalog_url) if store_data.catalog_url else None,
        is_active=store_data.is_active,
    )
    
    db.add(store)
    await db.commit()
    await db.refresh(store)
    
    logger.info(f"Created store: {store.name} (id={store.id})")
    
    return store


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing store.
    
    Only provided fields will be updated.
    """
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with id {store_id} not found",
        )
    
    # Update only provided fields
    update_data = store_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == 'chain' and value is not None:
            setattr(store, field, StoreChain(value.value))
        else:
            setattr(store, field, value)
    
    await db.commit()
    await db.refresh(store)
    
    logger.info(f"Updated store: {store.name} (id={store.id})")
    
    return store


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a store location.
    
    This will also delete all associated products and cache entries.
    """
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with id {store_id} not found",
        )
    
    await db.delete(store)
    await db.commit()
    
    logger.info(f"Deleted store: {store.name} (id={store_id})")
    
    return None


@router.get("/chains")
async def list_chains():
    """
    Get list of supported store chains.
    """
    return {
        "chains": [
            {"id": c.value, "name": _get_chain_display_name(c.value)}
            for c in StoreChain
        ]
    }


def _get_chain_display_name(chain_value: str) -> str:
    """Get human-readable name for a chain."""
    names = {
        "magnit": "Магнит",
        "pyaterochka": "Пятёрочка",
        "chizhik": "Чижик",
        "kb": "Красное & Белое",
        "custom": "Другой магазин",
    }
    return names.get(chain_value, chain_value.capitalize())
