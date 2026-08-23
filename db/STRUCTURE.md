# Database Service Structure

## 🎯 **Clean Architecture Overview**

This database service has been restructured with a clean, modular architecture that separates concerns and makes the codebase highly maintainable.

## 📁 **Directory Structure**

```
services/db/
├── app/                    # Application core
│   ├── __init__.py
│   ├── config.py          # Configuration management (pydantic-settings)
│   ├── factory.py         # Application factory pattern
│   └── startup.py         # Startup/shutdown events
├── routers/               # API route handlers (FastAPI routers)
│   ├── __init__.py
│   ├── telegram_peers.py
│   ├── telegram_channels.py
│   ├── users.py
│   ├── user_queries.py
│   ├── user_channels.py
│   ├── telegram_accounts.py
│   ├── rss_resources.py
│   └── twitter_channels.py
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── telegram_peers.py
│   ├── telegram_channels.py
│   ├── users.py
│   ├── user_queries.py
│   ├── user_channels.py
│   ├── telegram_accounts.py
│   ├── rss_resources.py
│   └── twitter_channels.py
├── schemas/               # Pydantic schemas (organized by domain)
│   ├── __init__.py
│   ├── base.py           # Base schema classes
│   ├── users.py
│   ├── telegram_peers.py
│   ├── telegram_channels.py
│   ├── user_queries.py
│   ├── user_channels.py
│   ├── telegram_accounts.py
│   ├── rss_resources.py
│   └── twitter_channels.py
├── tests/                 # Test suite (completely separate)
│   ├── __init__.py
│   ├── conftest.py       # Test configuration and fixtures
│   ├── test_telegram_peers.py
│   ├── test_telegram_channels.py
│   ├── test_users.py
│   └── [other test files...]
├── models.py              # SQLAlchemy ORM models
├── database.py            # Database configuration
├── main.py                # Application entry point
├── requirements.txt       # Dependencies
├── Dockerfile             # Container configuration
├── pytest.ini            # Pytest settings
├── run_tests.py           # Test runner
├── TESTING.md             # Testing documentation
└── README.md              # Main documentation
```

## 🏗️ **Architecture Principles**

### **1. Separation of Concerns**
- **Routers**: Handle HTTP requests/responses
- **Services**: Contain business logic
- **Schemas**: Define data validation and serialization
- **Models**: Define database structure
- **Tests**: Completely separate from application code

### **2. Clean Dependencies**
- Each layer has clear responsibilities
- Dependencies flow in one direction
- No circular dependencies
- Easy to test and maintain

### **3. Modular Design**
- Each entity has its own router, service, and schema files
- Easy to add new features
- Easy to modify existing features
- Clear boundaries between modules

## 🔧 **Key Components**

### **Application Factory (`app/factory.py`)**
```python
from app.factory import create_app

app = create_app()  # Creates and configures the FastAPI app
```

### **Configuration Management (`app/config.py`)**
```python
from app.config import settings

# Type-safe configuration with environment variable support
database_url = settings.database_url
```

### **Service Layer Pattern**
```python
from services.users import UsersService

service = UsersService(db_session)
users = await service.get_all_users()
```

### **Schema Organization**
```python
from schemas.users import User, UserCreate, UserUpdate
from schemas.telegram_peers import TelegramPeer, TelegramPeerCreate, TelegramPeerUpdate
```

### **Router Pattern**
```python
from routers.users import router as users_router

app.include_router(users_router, prefix="/api/v1")
```

## 🧪 **Testing Strategy**

### **Test Organization**
- **Separate `tests/` directory**: Keeps application code clean
- **Test database isolation**: Never touches production data
- **Transaction-based testing**: Each test runs in isolation
- **Comprehensive coverage**: All CRUD operations tested

### **Test Structure**
```
tests/
├── conftest.py           # Shared test fixtures
├── test_telegram_peers.py
├── test_telegram_channels.py
├── test_users.py
└── [other test files...]
```

### **Running Tests**
```bash
# Run all tests
python run_tests.py

# Run specific tests
pytest tests/test_users.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## 🔒 **Security & Safety**

### **Database Safety**
- **Separate test database**: `test_db` vs production database
- **Transaction rollback**: All test changes are undone
- **Environment isolation**: Test and production environments are separate

### **Thread Safety**
- **Shared database lock**: `asyncio.Lock()` across all routers
- **Connection pooling**: Proper database connection management
- **Error handling**: Comprehensive error handling with proper HTTP status codes

## 📊 **Benefits of This Structure**

### **1. Maintainability**
- Clear separation of concerns
- Easy to find and modify code
- Consistent patterns across the codebase

### **2. Testability**
- Easy to write unit tests
- Easy to mock dependencies
- Comprehensive test coverage

### **3. Scalability**
- Easy to add new features
- Easy to modify existing features
- Clear boundaries between modules

### **4. Safety**
- Production data is never touched by tests
- Comprehensive validation
- Proper error handling

### **5. Developer Experience**
- Clear file organization
- Consistent naming conventions
- Comprehensive documentation

## 🚀 **Adding New Features**

### **1. Create Schema**
```python
# schemas/new_entity.py
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema

class NewEntity(BaseSchema):
    id: int
    name: str

class NewEntityCreate(BaseCreateSchema):
    name: str

class NewEntityUpdate(BaseUpdateSchema):
    name: Optional[str] = None
```

### **2. Create Service**
```python
# services/new_entity.py
from models import NewEntity
from schemas.new_entity import NewEntityCreate, NewEntityUpdate

class NewEntityService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all(self) -> List[NewEntity]:
        return self.db.query(NewEntity).all()
```

### **3. Create Router**
```python
# routers/new_entity.py
from services.new_entity import NewEntityService
from schemas.new_entity import NewEntity, NewEntityCreate, NewEntityUpdate

router = APIRouter()
db_lock = asyncio.Lock()

@router.get("/new-entities", response_model=List[NewEntity])
async def get_new_entities(db: Session = Depends(get_db)):
    async with db_lock:
        service = NewEntityService(db)
        return await service.get_all()
```

### **4. Add to Factory**
```python
# app/factory.py
from routers import new_entity

app.include_router(
    new_entity.router,
    prefix=f"{settings.api_prefix}",
    tags=["New Entity"]
)
```

### **5. Write Tests**
```python
# tests/test_new_entity.py
class TestNewEntityAPI:
    @pytest.mark.asyncio
    async def test_get_new_entities(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/new-entities")
        assert response.status_code == 200
```

## 📝 **Best Practices**

### **1. Code Organization**
- Keep related code together
- Use consistent naming conventions
- Follow the established patterns

### **2. Testing**
- Write tests for all new features
- Use the existing test fixtures
- Ensure test isolation

### **3. Documentation**
- Update documentation when adding features
- Use clear, descriptive names
- Add docstrings to functions and classes

### **4. Error Handling**
- Use proper HTTP status codes
- Provide meaningful error messages
- Handle edge cases gracefully

This structure provides a solid foundation for a maintainable, scalable, and safe database service. 