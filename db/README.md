# Database Service

A FastAPI-based database service with a clean, modular architecture for managing various data entities including users, telegram channels, RSS resources, and more.

## 🏗️ Architecture

The application follows a clean, modular architecture with clear separation of concerns:

```
services/db/
├── app/                    # Application core
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── factory.py         # Application factory
│   └── startup.py         # Startup/shutdown events
├── routers/               # API route handlers
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
│   ├── base.py
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
│   ├── conftest.py
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
└── TESTING.md             # Testing documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL
- Docker (optional)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd services/db
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Docker Setup

```bash
# Start the database service
docker-compose up db_services

# Or start with test database
docker-compose up test_db
```

## 📋 API Endpoints

### Users
- `GET /api/v1/users` - Get all users
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users` - Update user
- `DELETE /api/v1/users` - Delete user

### Telegram Peers
- `GET /api/v1/telegram/peers` - Get telegram peers
- `POST /api/v1/telegram/peers` - Create telegram peer
- `PUT /api/v1/telegram/peers` - Update telegram peer
- `DELETE /api/v1/telegram/peers` - Delete telegram peer

### Telegram Channels
- `GET /api/v1/telegram/channels` - Get telegram channels
- `POST /api/v1/telegram/channels` - Create telegram channel
- `PUT /api/v1/telegram/channels` - Update telegram channel
- `DELETE /api/v1/telegram/channels` - Delete telegram channel

### User Queries
- `GET /api/v1/users/queries` - Get user queries
- `POST /api/v1/users/queries` - Create user query
- `PUT /api/v1/users/queries` - Update user query
- `DELETE /api/v1/users/queries` - Delete user query

### User Channels
- `GET /api/v1/users/channels` - Get user channels
- `POST /api/v1/users/channels` - Create user channel
- `PUT /api/v1/users/channels/{id}` - Update user channel
- `DELETE /api/v1/users/channels/{id}` - Delete user channel

### Telegram Accounts
- `GET /api/v1/telegram/accounts` - Get telegram accounts
- `POST /api/v1/telegram/accounts` - Create telegram accounts
- `PUT /api/v1/telegram/accounts/{id}` - Update telegram account
- `DELETE /api/v1/telegram/accounts/{id}` - Delete telegram account

### RSS Resources
- `GET /api/v1/rss/channels` - Get RSS resources
- `POST /api/v1/rss/channels` - Create RSS resources
- `PUT /api/v1/rss/channels/{id}` - Update RSS resource
- `DELETE /api/v1/rss/channels/{id}` - Delete RSS resource

### Twitter Channels
- `GET /api/v1/twitter/channels` - Get twitter channels
- `POST /api/v1/twitter/channels` - Create twitter channels
- `PUT /api/v1/twitter/channels/{id}` - Update twitter channel
- `DELETE /api/v1/twitter/channels/{id}` - Delete twitter channel

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python run_tests.py

# Run specific test file
pytest tests/test_telegram_peers.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Database

The application uses a separate test database to ensure your production data is safe:

- **Production Database**: Uses `POSTGRES_DB` from environment
- **Test Database**: Uses `test_db` database
- **Isolation**: Each test runs in a transaction that gets rolled back

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Test Database Configuration
TEST_POSTGRES_DB=test_db
TEST_POSTGRES_HOST=localhost

# Application Configuration
TESTING=false
DEBUG=false
APP_NAME="Database Service"
APP_VERSION="1.0.0"
API_PREFIX="/api/v1"
```

### Configuration Management

The application uses `pydantic-settings` for configuration management:

- **Environment-based**: Automatically loads from `.env` files
- **Type-safe**: All settings are validated at startup
- **Flexible**: Supports different environments (dev, test, prod)

## 🏛️ Architecture Details

### Application Factory Pattern

The application uses a factory pattern for clean dependency injection:

```python
from app.factory import create_app

app = create_app()
```

### Service Layer

Business logic is separated into service classes:

```python
from services.users import UsersService

service = UsersService(db_session)
users = await service.get_all_users()
```

### Schema Organization

Pydantic schemas are organized by domain for better maintainability:

```python
from schemas.users import User, UserCreate, UserUpdate
from schemas.telegram_peers import TelegramPeer, TelegramPeerCreate, TelegramPeerUpdate
```

### Router Organization

API routes are organized by domain:

- Each router handles a specific entity type
- Consistent CRUD operations across all routers
- Shared database lock for thread safety

### Database Lock

The application uses a shared `asyncio.Lock()` across all routers to ensure thread safety:

```python
db_lock = asyncio.Lock()

async def some_operation():
    async with db_lock:
        # Database operations here
        pass
```

## 🔒 Security Features

- **Input Validation**: All inputs are validated using Pydantic schemas
- **SQL Injection Protection**: Uses SQLAlchemy ORM with parameterized queries
- **Environment Isolation**: Separate test and production databases
- **Error Handling**: Comprehensive error handling with proper HTTP status codes

## 📊 Database Models

The application includes the following main models:

- **User**: User accounts and authentication
- **TelegramPeer**: Telegram peer information
- **TelegramChannel**: Telegram channel data
- **UserQueries**: User search queries
- **UserChannels**: User channel subscriptions
- **TelegramAccount**: Telegram account management
- **RSSResource**: RSS feed resources
- **TwitterChannel**: Twitter channel data

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t db-service .
docker run -p 8000:8000 db-service
```

### Production Considerations

1. **Environment Variables**: Use proper secrets management
2. **Database**: Use production-grade PostgreSQL
3. **Logging**: Configure proper logging
4. **Monitoring**: Add health checks and metrics
5. **Security**: Configure CORS and authentication

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features in the `tests/` directory
3. Update documentation
4. Use the testing framework to ensure data safety

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the [TESTING.md](TESTING.md) for testing-related issues
2. Review the API documentation at `/docs` when the service is running
3. Check the logs for detailed error information
