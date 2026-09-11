"""
API Router that combines all endpoint routers.
"""
from fastapi import APIRouter

from app.api.routes import stores, search, products, shopping_lists, favorites


# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(stores.router, prefix="/stores", tags=["Stores"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(shopping_lists.router, prefix="/shopping-lists", tags=["Shopping Lists"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
