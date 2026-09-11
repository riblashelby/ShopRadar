import random
from typing import List, Optional
from datetime import datetime
from app.db.models import Product
from app.parsers.base import BaseParser

class MagnitParser(BaseParser):
    """
    Парсер для магазинов 'Магнит'.
    
    ВНИМАНИЕ: Прямой парсинг сайта eda.yandex.ru затруднен из-за:
    1. Динамической подгрузки контента (React SPA).
    2. Сложной системы защиты от ботов и токенов сессии.
    
    Для демонстрации работы системы используется режим симуляции (Mock),
    генерирующий реалистичные цены на основе средних рыночных данных.
    Для продакшена рекомендуется использование официального API партнеров 
    или обратный инжиниринг внутренних GraphQL запросов мобильного приложения.
    """

    def __init__(self, store_id: str, catalog_url: Optional[str] = None):
        self.store_id = store_id
        self.catalog_url = catalog_url
        # Базовые цены для симуляции (цена за единицу измерения)
        self.base_prices = {
            "кола": 89.90,
            "молоко": 119.90,
            "хлеб": 65.00,
            "яйца": 120.00,
            "курица": 350.00,
            "гречка": 85.00,
            "вода": 45.00,
            "пиво": 180.00,
            "шоколад": 150.00,
            "сыр": 600.00,
        }

    async def search_products(self, query: str) -> List[Product]:
        """
        Имитирует поиск товаров в каталоге Магнита.
        Генерирует 3-6 вариантов товара с разными объемами и ценами.
        """
        results = []
        query_lower = query.lower()
        
        # Определяем базовую цену или используем случайную, если товар не найден в базе
        base_price = self.base_prices.get(query_lower, random.uniform(50, 500))
        
        # Количество результатов для симуляции
        num_results = random.randint(3, 6)
        
        brands = ["Красная Цена", "Магнит", "Каждый День", "Fruit Bay", "365 дней", "Teador", "Coca-Cola", "Pepsi"]
        volumes = [
            {"val": 0.33, "unit": "l"}, {"val": 0.5, "unit": "l"}, {"val": 1.0, "unit": "l"},
            {"val": 180, "unit": "g"}, {"val": 400, "unit": "g"}, {"val": 900, "unit": "g"},
            {"val": 10, "unit": "pcs"}, {"val": 20, "unit": "pcs"}
        ]
        
        for i in range(num_results):
            brand = random.choice(brands)
            vol_info = random.choice(volumes)
            
            # Расчет цены с небольшим разбросом (+- 15%)
            variance = random.uniform(0.85, 1.15)
            price = round(base_price * vol_info["val"] * variance, 2)
            if vol_info["unit"] == "pcs":
                price = round(base_price * variance, 2) # Для штук цена фиксированнее
            
            # Расчет удельной цены
            unit_price = round(price / vol_info["val"], 2) if vol_info["val"] > 0 else 0.0
            
            product_name = f"{brand} {query} {vol_info['val']}{vol_info['unit']}"
            
            product = Product(
                store_id=self.store_id,
                name=product_name,
                brand=brand,
                price=price,
                volume=vol_info["val"],
                volume_unit=vol_info["unit"],
                unit_price=unit_price,
                url=f"{self.catalog_url}?search={query}&item={i}",
                image_url="https://via.placeholder.com/150?text=Product", # Заглушка
                parsed_at=datetime.utcnow()
            )
            results.append(product)
            
        return results

    async def get_store_info(self) -> dict:
        return {
            "store_id": self.store_id,
            "name": "Магнит",
            "status": "active",
            "source": "mock_simulation"
        }
