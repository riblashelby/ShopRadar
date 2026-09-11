# CheapCart Backend Application

Self-hosted price comparison web application for grocery stores.

## Quick Start

```bash
# Build and run with Docker
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Architecture

```
backend/
├── app/
│   ├── api/           # FastAPI routes
│   │   ├── routes/    # Endpoint modules
│   │   └── router.py  # Main API router
│   ├── db/            # Database layer
│   │   ├── models.py  # SQLAlchemy ORM models
│   │   └── database.py # DB connection
│   ├── parsers/       # Store-specific parsers
│   │   ├── base.py    # Base parser interface
│   │   ├── factory.py # Parser registry & factory
│   │   └── pyaterochka_parser.py  # Example parser
│   ├── services/      # Business logic
│   │   └── parser_service.py
│   ├── config.py      # Application settings
│   ├── main.py        # FastAPI app entry point
│   └── schemas.py     # Pydantic models
├── data/              # SQLite database (created at runtime)
├── requirements.txt   # Python dependencies
└── Dockerfile

frontend/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   └── App.jsx        # Main app component
├── public/
├── package.json
└── Dockerfile
```

## Supported Store Chains

Currently implemented:
- **Пятёрочка** (Pyaterochka) - Demo parser included

To add more stores, create a new parser class extending `BaseParser`:

```python
# backend/app/parsers/magnit_parser.py
from app.parsers.base import BaseParser, ProductData

class MagnitParser(BaseParser):
    CHAIN_NAME = "magnit"
    SUPPORTED_DOMAINS = ["magnit.ru"]
    
    async def search_products(self, query: str) -> List[ProductData]:
        # Implement parsing logic
        pass
```

Then register it in `parsers/factory.py`:

```python
from app.parsers.magnit_parser import MagnitParser
ParserRegistry.register(StoreChain.MAGNIT.value, MagnitParser)
```

## API Endpoints

### Stores
- `GET /api/v1/stores` - List all stores
- `POST /api/v1/stores` - Create new store
- `GET /api/v1/stores/{id}` - Get store details
- `PUT /api/v1/stores/{id}` - Update store
- `DELETE /api/v1/stores/{id}` - Delete store
- `GET /api/v1/stores/chains` - List supported chains

### Search
- `POST /api/v1/search` - Search products across stores
- `GET /api/v1/search/history` - Get search history

### Products
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/products/store/{store_id}` - Get store products

### Shopping Lists
- `GET /api/v1/shopping-lists` - List shopping lists
- `POST /api/v1/shopping-lists` - Create shopping list
- `PUT /api/v1/shopping-lists/{id}` - Update list
- `DELETE /api/v1/shopping-lists/{id}` - Delete list

### Favorites
- `GET /api/v1/favorites` - List favorites
- `POST /api/v1/favorites` - Add favorite
- `DELETE /api/v1/favorites/{id}` - Remove favorite

## Configuration

Environment variables (via `.env` file):

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

## Development

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

## Adding New Parsers

1. **Find the API/HTML structure:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Visit store website and search for a product
   - Look for XHR/Fetch requests with product data

2. **Create parser class:**

```python
from app.parsers.base import BaseParser, ProductData
import httpx
from bs4 import BeautifulSoup

class NewStoreParser(BaseParser):
    CHAIN_NAME = "newstore"
    SUPPORTED_DOMAINS = ["newstore.ru"]
    
    async def search_products(self, query: str) -> List[ProductData]:
        # Use API if available
        # Or parse HTML with BeautifulSoup
        pass
```

3. **Register parser** in `parsers/factory.py`

4. **Test** using the API docs at `/docs`

## License

MIT
