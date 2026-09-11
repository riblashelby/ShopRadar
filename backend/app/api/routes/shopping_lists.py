"""
Shopping list endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.db.models import ShoppingList, Store
from app.schemas import (
    ShoppingListCreate,
    ShoppingListResponse,
    ShoppingListItem,
)
from loguru import logger

router = APIRouter()


@router.get("", response_model=List[ShoppingListResponse])
async def list_shopping_lists(db: AsyncSession = Depends(get_db)):
    """
    Get all shopping lists.
    """
    result = await db.execute(
        select(ShoppingList).order_by(ShoppingList.updated_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    data: ShoppingListCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new shopping list.
    
    - **name**: List name
    - **items**: List of items with name, quantity, and optional store info
    """
    # Calculate total cost
    total_cost = sum(
        (item.best_price or 0) * item.quantity
        for item in data.items
    )
    
    # Convert items to JSON-serializable format
    items_data = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "best_price": item.best_price,
            "store_id": item.store_id,
            "store_name": item.store_name,
        }
        for item in data.items
    ]
    
    shopping_list = ShoppingList(
        name=data.name,
        items=items_data,
        total_cost=total_cost,
    )
    
    db.add(shopping_list)
    await db.commit()
    await db.refresh(shopping_list)
    
    logger.info(f"Created shopping list: {shopping_list.name}")
    
    return shopping_list


@router.get("/{list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(list_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific shopping list.
    """
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.id == list_id)
    )
    shopping_list = result.scalar_one_or_none()
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with id {list_id} not found",
        )
    
    return shopping_list


@router.put("/{list_id}", response_model=ShoppingListResponse)
async def update_shopping_list(
    list_id: int,
    data: ShoppingListCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing shopping list.
    """
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.id == list_id)
    )
    shopping_list = result.scalar_one_or_none()
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with id {list_id} not found",
        )
    
    # Update fields
    shopping_list.name = data.name
    
    # Convert items to JSON-serializable format
    items_data = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "best_price": item.best_price,
            "store_id": item.store_id,
            "store_name": item.store_name,
        }
        for item in data.items
    ]
    shopping_list.items = items_data
    
    # Recalculate total
    shopping_list.total_cost = sum(
        (item.best_price or 0) * item.quantity
        for item in data.items
    )
    
    await db.commit()
    await db.refresh(shopping_list)
    
    return shopping_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(list_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a shopping list.
    """
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.id == list_id)
    )
    shopping_list = result.scalar_one_or_none()
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with id {list_id} not found",
        )
    
    await db.delete(shopping_list)
    await db.commit()
    
    logger.info(f"Deleted shopping list: {shopping_list.name}")
    
    return None
