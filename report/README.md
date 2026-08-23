# Reporting Data API

A FastAPI-based application for analyzing Fetched data from (Telegram, RSS, Twitter, Instagram, ...) with improved architecture and code organization.

## 🏗️ Project Structure

```
services/report/
├── app/                          # Application factory and configuration
│   ├── __init__.py
│   └── factory.py               # FastAPI app factory
├── auth/                        # Authentication and authorization
│   └── auth.py
├── config.py                    # Configuration settings
├── main.py                      # Application entry point
├── startup.py                   # Startup dependencies (Elasticsearch, Kafka)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── README.md                    # This file
├── routers/                     # API route handlers
│   ├── __init__.py
│   ├── platform.py             # Platform router (includes all platform routers)
│   ├── actions/                # User action routers
│   │   ├── user_query.py
│   │   ├── user_channel.py
│   │   └── user.py
│   └── telegram/               # Telegram-specific routers
│       ├── __init__.py         # Main telegram router
│       ├── channels.py         # Channel-related endpoints
│       ├── groups.py           # Group-related endpoints
│       ├── trends.py           # Trend analysis endpoints
│       ├── wordcloud.py        # Wordcloud generation endpoints
│       └── posts.py            # Post and comment endpoints
├── services/                    # Business logic layer
│   ├── __init__.py
│   ├── services.py             # General utility services
│   └── telegram_service.py     # Telegram-specific business logic
├── schemas/                     # Pydantic data models
│   ├── __init__.py
│   ├── schemas.py              # General schemas
│   ├── telegram_schemas.py     # Telegram-specific schemas
│   ├── user_schema.py          # User-related schemas
│   ├── user_channel_schema.py  # User channel schemas
│   ├── user_query_schema.py    # User query schemas
│   └── admin_schemas.py        # Admin-related schemas
├── queries/                     # Query templates and definitions
│   └── queries.py
├── docs/                        # API documentation
└── tests/                       # Test files
```

## 🚀 Key Improvements

### 1. **Eliminated Code Duplication**
- **Before**: Two nearly identical functions `get_fa_channels_list` and `get_fa_groups_list` with 90% duplicate code
- **After**: Single generic `get_entity_list` method in `TelegramService` that handles both channels and groups

### 2. **Separation of Concerns**
- **Business Logic**: Moved to dedicated service classes (`TelegramService`)
- **API Endpoints**: Organized into focused router modules
- **Data Models**: Properly structured in schemas directory
- **Configuration**: Centralized in factory pattern

### 3. **Modular Router Structure**
- Split large `telegram.py` file (610 lines) into focused modules:
  - `channels.py` - Channel-related endpoints
  - `groups.py` - Group-related endpoints  
  - `trends.py` - Trend analysis
  - `wordcloud.py` - Wordcloud generation
  - `posts.py` - Post and comment handling

### 4. **Service Layer Architecture**
- Created `TelegramService` class with reusable methods
- Generic `get_entity_list` method handles both channels and groups
- Helper methods for building queries and aggregations
- Better error handling and validation

### 5. **Factory Pattern**
- Application creation moved to `app/factory.py`
- Better testability and configuration management
- Cleaner main.py entry point

## 📋 API Endpoints

### Telegram Channels
- `GET /platform/telegram/fa/channels/list` - List channels with search/pagination
- `GET /platform/telegram/fa/channels/{channel_id}` - Get channel details
- `GET /platform/telegram/fa/channels/image` - Get channel image

### Telegram Groups  
- `GET /platform/telegram/fa/groups/list` - List groups with search/pagination
- `GET /platform/telegram/fa/groups/{group_id}` - Get group details
- `GET /platform/telegram/fa/groups/image` - Get group image

### Trends & Analysis
- `POST /platform/telegram/trends/` - Get top trends
- `POST /platform/telegram/trends/histogram/publish` - Get histogram data
- `POST /platform/telegram/fa/wordcloud/` - Generate wordcloud

### Posts & Comments
- `POST /platform/telegram/fa/channelspost` - Get channel posts
- `POST /platform/telegram/fa/channelscomment` - Get channel comments

## 🔧 Usage

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Development
```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

The new structure makes testing much easier:

```python
# Test the service layer independently
from services.telegram_service import TelegramService

# Test specific routers
from routers.telegram.channels import router as channels_router
```

## 📈 Benefits

1. **Maintainability**: Code is now organized by functionality
2. **Reusability**: Common logic extracted to service layer
3. **Testability**: Each component can be tested independently
4. **Scalability**: Easy to add new features without affecting existing code
5. **Readability**: Clear separation of concerns makes code easier to understand

## 🔄 Migration Notes

The refactored code maintains backward compatibility with existing API contracts while providing a much cleaner internal structure. All existing endpoints continue to work as before, but the underlying implementation is now more maintainable and extensible. 
