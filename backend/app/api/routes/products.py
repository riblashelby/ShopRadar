"""
Product endpoints for direct product access.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.db.models import Product, Store
from app.schemas import ProductResponse

router = APIRouter()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific product by ID.
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    
    # Get store info
    store_result = await db.execute(
        select(Store).where(Store.id == product.store_id)
    )
    store = store_result.scalar_one_or_none()
    
    return ProductResponse(
        id=product.id,
        store_id=product.store_id,
        store_name=store.name if store else None,
        store_address=store.address if store else None,
        name=product.name,
        brand=product.brand,
        price=product.price,
        volume=product.volume,
        volume_unit=product.volume_unit,
        unit_price=product.unit_price,
        url=product.url,
        image_url=product.image_url,
        query=product.query,
        parsed_at=product.parsed_at,
    )


@router.get("/store/{store_id}", response_model=List[ProductResponse])
async def get_store_products(
    store_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Get products from a specific store.
    """
    result = await db.execute(
        select(Product)
        .where(Product.store_id == store_id)
        .order_by(Product.parsed_at.desc())
        .limit(limit)
    )
    products = list(result.scalars().all())
    
    # Get store info
    store_result = await db.execute(
        select(Store).where(Store.id == store_id)
    )
    store = store_result.scalar_one_or_none()
    
    return [
        ProductResponse(
            id=p.id,
            store_id=p.store_id,
            store_name=store.name if store else None,
            store_address=store.address if store else None,
            name=p.name,
            brand=p.brand,
            price=p.price,
            volume=p.volume,
            volume_unit=p.volume_unit,
            unit_price=p.unit_price,
            url=p.url,
            image_url=p.image_url,
            query=p.query,
            parsed_at=p.parsed_at,
        )
        for p in products
    ]
