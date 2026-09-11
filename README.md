# CheapCart - Сравнение цен на продукты питания

Self-hosted веб-приложение для сравнения цен на продукты в ближайших магазинах.

## 🎯 Возможности

- **Поиск товаров** по названию (например, "кола", "молоко", "гречка")
- **Сравнение цен** с автоматической нормализацией (цена за литр/кг)
- **Нечёткий поиск** - находит похожие товары даже при неточном запросе
- **Кэширование результатов** - быстрый повторный поиск
- **Списки покупок** - планируйте покупки с оптимальными ценами
- **Избранное** - отслеживайте лучшие цены на любимые товары
- **Мобильный UI** - удобно использовать с телефона в магазине

## 🚀 Быстрый старт

```bash
# Клонировать репозиторий
git clone <repository-url>
cd cheapcart

# Запустить через Docker Compose
docker-compose up -d

# Открыть в браузере
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📁 Структура проекта

```
cheapcart/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   │   ├── routes/     # Route modules
│   │   │   └── router.py   # Main router
│   │   ├── db/             # Database layer
│   │   │   ├── models.py   # SQLAlchemy ORM
│   │   │   └── database.py # DB connection
│   │   ├── parsers/        # Store-specific parsers
│   │   │   ├── base.py     # Base parser interface
│   │   │   ├── factory.py  # Parser registry
│   │   │   └── pyaterochka_parser.py
│   │   ├── services/       # Business logic
│   │   │   └── parser_service.py
│   │   ├── config.py       # Settings
│   │   ├── main.py         # FastAPI app
│   │   └── schemas.py      # Pydantic models
│   ├── data/               # SQLite database (auto-created)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── api.js          # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🏪 Поддерживаемые магазины

На данный момент реализованы парсеры:
- **Пятёрочка** (5ka.ru) - базовый парсер

### Как добавить новый магазин

1. Создайте файл парсера в `backend/app/parsers/`:

```python
# backend/app/parsers/magnit_parser.py
from app.parsers.base import BaseParser, ProductData
import httpx
from bs4 import BeautifulSoup

class MagnitParser(BaseParser):
    CHAIN_NAME = "magnit"
    SUPPORTED_DOMAINS = ["magnit.ru"]
    
    async def search_products(self, query: str) -> list[ProductData]:
        # Реализуйте логику парсинга
        pass
```

2. Зарегистрируйте парсер в `backend/app/parsers/factory.py`:

```python
from app.parsers.magnit_parser import MagnitParser

def init_registry():
    ParserRegistry.register(StoreChain.MAGNIT.value, MagnitParser)
    # ... другие парсеры
```

3. Перезапустите приложение: `docker-compose restart backend`

### Поиск API эндпоинтов магазинов

Для добавления новых парсеров:
1. Откройте DevTools браузера (F12)
2. Перейдите на вкладку Network
3. Посетите сайт магазина и выполните поиск товара
4. Найдите XHR/Fetch запросы с данными о товарах
5. Изучите формат запроса/ответа

## 🔧 Конфигурация

Создайте файл `.env` в корне проекта:

```env
# Application
APP_NAME=CheapCart
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cheapcart.db

# Server
HOST=0.0.0.0
PORT=8000

# Parser settings
CACHE_TTL_HOURS=6
REQUEST_DELAY_MS=500
MAX_RETRIES=3
REQUEST_TIMEOUT_SEC=30
```

## 📊 API Endpoints

### Магазины
- `GET /api/v1/stores` - Список всех магазинов
- `POST /api/v1/stores` - Создать магазин
- `GET /api/v1/stores/{id}` - Информация о магазине
- `PUT /api/v1/stores/{id}` - Обновить магазин
- `DELETE /api/v1/stores/{id}` - Удалить магазин
- `GET /api/v1/stores/chains` - Список поддерживаемых сетей

### Поиск
- `POST /api/v1/search` - Поиск товаров
- `GET /api/v1/search/history` - История поиска

### Товары
- `GET /api/v1/products/{id}` - Информация о товаре
- `GET /api/v1/products/store/{store_id}` - Товары магазина

### Списки покупок
- `GET /api/v1/shopping-lists` - Список покупок
- `POST /api/v1/shopping-lists` - Создать список
- `PUT /api/v1/shopping-lists/{id}` - Обновить список
- `DELETE /api/v1/shopping-lists/{id}` - Удалить список

### Избранное
- `GET /api/v1/favorites` - Избранные товары
- `POST /api/v1/favorites` - Добавить в избранное
- `DELETE /api/v1/favorites/{id}` - Удалить из избранного

## 💻 Разработка

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🐳 Docker

### Сборка образов

```bash
docker-compose build
```

### Запуск

```bash
docker-compose up -d
```

### Просмотр логов

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Остановка

```bash
docker-compose down
```

### Сохранение данных

Данные SQLite хранятся в volume `cheapcart_data`. Для экспорта:

```bash
docker cp $(docker ps -q -f name=cheapcart-backend-1):/app/data/cheapcart.db ./backup.db
```

## 📱 Использование

1. **Добавьте магазины**: Перейдите на страницу "Магазины" и добавьте ваши любимые торговые точки
2. **Выполните поиск**: Введите название товара на главной странице
3. **Сравните цены**: Результаты отсортированы по удельной цене (лучшие предложения сверху)
4. **Сохраните в избранное**: Нажмите на товар, чтобы сохранить лучшую цену
5. **Создайте список покупок**: Добавьте несколько товаров для оптимизации маршрута

## ⚠️ Важные замечания

- Парсеры могут требовать обновления при изменении структуры сайтов магазинов
- Уважайте robots.txt и условия использования сайтов
- Для продакшена настройте CORS и rate limiting
- Рекомендуется использовать внешнюю базу данных (PostgreSQL) для больших объёмов данных

## 🛠 Технологии

- **Backend**: Python, FastAPI, SQLAlchemy, aiohttp, BeautifulSoup4
- **Frontend**: React, Vite, TailwindCSS, React Query, Axios
- **Database**: SQLite (по умолчанию), поддержка PostgreSQL
- **Deployment**: Docker, Docker Compose

## 📄 Лицензия

MIT