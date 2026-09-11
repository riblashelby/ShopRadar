"""
Favorite items endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.db.models import FavoriteItem, Store
from app.schemas import FavoriteItemCreate, FavoriteItemResponse
from loguru import logger

router = APIRouter()


@router.get("", response_model=List[FavoriteItemResponse])
async def list_favorites(db: AsyncSession = Depends(get_db)):
    """
    Get all favorite items.
    """
    result = await db.execute(
        select(FavoriteItem).order_by(FavoriteItem.added_at.desc())
    )
    favorites = list(result.scalars().all())
    
    # Enrich with store names
    responses = []
    for fav in favorites:
        store_name = None
        if fav.best_store_id:
            store_result = await db.execute(
                select(Store.name).where(Store.id == fav.best_store_id)
            )
            store = store_result.scalar_one_or_none()
            store_name = store
        
        responses.append(FavoriteItemResponse(
            id=fav.id,
            product_name=fav.product_name,
            best_price=fav.best_price,
            best_store_id=fav.best_store_id,
            best_store_name=store_name,
            added_at=fav.added_at,
        ))
    
    return responses


@router.post("", response_model=FavoriteItemResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    data: FavoriteItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add an item to favorites.
    """
    favorite = FavoriteItem(
        product_name=data.product_name,
        best_price=data.best_price,
        best_store_id=data.best_store_id,
    )
    
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    
    # Get store name
    store_name = None
    if favorite.best_store_id:
        store_result = await db.execute(
            select(Store.name).where(Store.id == favorite.best_store_id)
        )
        store = store_result.scalar_one_or_none()
        store_name = store
    
    logger.info(f"Added favorite: {favorite.product_name}")
    
    return FavoriteItemResponse(
        id=favorite.id,
        product_name=favorite.product_name,
        best_price=favorite.best_price,
        best_store_id=favorite.best_store_id,
        best_store_name=store_name,
        added_at=favorite.added_at,
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    Remove an item from favorites.
    """
    result = await db.execute(
        select(FavoriteItem).where(FavoriteItem.id == item_id)
    )
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorite item with id {item_id} not found",
        )
    
    await db.delete(favorite)
    await db.commit()
    
    logger.info(f"Deleted favorite: {favorite.product_name}")
    
    return None
