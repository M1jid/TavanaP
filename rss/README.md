# RSS Feed Processing Service

A production-ready RSS feed processing service built with FastAPI, designed to fetch, process, and distribute RSS feed content through Kafka and other messaging systems.

## 🏗️ Architecture

This service follows clean architecture principles with proper separation of concerns:

```
services/rss/
├── app/
│   ├── __init__.py              # App package initialization
│   ├── main.py                  # Application entry point
│   ├── factory.py               # FastAPI application factory
│   ├── config.py                # Configuration management
│   ├── startup.py               # Service startup and initialization
│   ├── models/                  # Data models and schemas
│   │   ├── __init__.py
│   │   └── feed_models.py       # RSS feed data models
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── rss_service.py       # Main RSS service orchestrator
│   │   ├── feed_fetcher.py      # RSS feed fetching service
│   │   ├── feed_processor.py    # Feed processing and distribution
│   │   └── message_extractor.py # Message extraction and formatting
│   ├── schemas/                 # API request/response schemas
│   │   ├── __init__.py
│   │   └── rss_schemas.py       # Pydantic schemas for validation
│   └── routers/                 # API route handlers
│       ├── __init__.py
│       └── rss_router.py        # RSS API endpoints
├── Dockerfile                   # Container configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Features

- **Clean Architecture**: Proper separation of concerns with services, models, and routers
- **Async Processing**: Non-blocking RSS feed fetching and processing
- **Error Handling**: Comprehensive error handling and logging
- **API Documentation**: Auto-generated OpenAPI documentation
- **Health Monitoring**: Built-in health checks and service statistics
- **Message Distribution**: Integration with Kafka for message routing
- **Data Persistence**: Storage in KSQL and Redis for caching
- **Proxy Support**: Configurable proxy support for feed fetching

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd services/rss
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file with the following configuration:
   ```env
   # Kafka Configuration
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   
   # KSQL Configuration
   KSQL_HOST=localhost:8088
   RSS_STREAMS_PATH=/path/to/streams.json
   RSS_CONNECTOR_PATH=/path/to/connectors.json
   
   # Elasticsearch Configuration
   ELASTIC_URL=http://localhost:9200
   ELASTIC_USERNAME=elastic
   ELASTIC_PASSWORD=password
   RSS_ELASTIC_INDEX_MAPPING_PATH=/path/to/mappings.json
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # Proxy Configuration (optional)
   PROXY_HOST=proxy.example.com
   PROXY_PORT=8080
   PROXY_PROTOCOL=socks5h
   
   # Authentication
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Run the service**:
   ```bash
   python -m app.main
   ```

## 🐳 Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t rss-service .

# Run the container
docker run -p 8000:8000 --env-file .env rss-service
```

## 📡 API Endpoints

### Health and Status
- `GET /rss/status` - Service health check
- `GET /rss/info` - Detailed service information

### RSS Channel Management
- `GET /rss/api/v1/channels` - List all RSS channels
- `POST /rss/api/v1/channels` - Add new RSS channel
- `GET /rss/api/v1/channels/{key}` - Get specific channel details
- `DELETE /rss/api/v1/channels/{key}` - Remove RSS channel
- `POST /rss/api/v1/channels/{key}/refresh` - Manually refresh channel

### Service Control
- `GET /rss/api/v1/statistics` - Get processing statistics
- `POST /rss/api/v1/pause` - Pause RSS processing
- `POST /rss/api/v1/resume` - Resume RSS processing

### API Documentation
- `GET /rss/docs` - Interactive API documentation (Swagger UI)
- `GET /rss/redoc` - Alternative API documentation (ReDoc)

## 🔧 Configuration

### RSS Channel Configuration

To add an RSS channel, send a POST request to `/rss/api/v1/channels`:

```json
{
  "key": "example_news",
  "title": "Example News",
  "rss_url": "https://example.com/rss.xml",
  "website_url": "https://example.com",
  "description": "Example news channel",
  "language": "en"
}
```

### Processing Configuration

The service automatically processes RSS feeds every 120 seconds. You can:

- **Pause processing**: `POST /rss/api/v1/pause`
- **Resume processing**: `POST /rss/api/v1/resume`
- **Manual refresh**: `POST /rss/api/v1/channels/{key}/refresh`

## 📊 Monitoring

### Service Statistics

Get detailed statistics about RSS processing:

```bash
curl http://localhost:8000/rss/api/v1/statistics
```

Response includes:
- Total feeds processed
- Total messages sent
- Error count
- Last processing time
- Service uptime

### Health Checks

Monitor service health:

```bash
curl http://localhost:8000/rss/status
```

## 🏭 Service Architecture

### Core Services

1. **RSSService**: Main orchestrator that manages the entire RSS processing pipeline
2. **FeedFetcher**: Handles RSS feed fetching with error handling and retry logic
3. **FeedProcessor**: Processes feed entries and distributes messages
4. **MessageExtractor**: Extracts and formats RSS entries into structured messages

### Data Flow

1. **Feed Discovery**: Service retrieves RSS channel configurations from database
2. **Feed Fetching**: Concurrent fetching of RSS feeds using aiohttp
3. **Message Processing**: Extraction and formatting of feed entries
4. **Deduplication**: Redis-based deduplication to avoid processing duplicate entries
5. **Distribution**: Messages sent to Kafka for further processing
6. **Storage**: Processed messages stored in KSQL database

### Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **Invalid Feeds**: Graceful handling of malformed RSS feeds
- **Service Failures**: Comprehensive logging and error reporting
- **Resource Limits**: Proper timeout handling and resource cleanup

## 🔒 Security

- **Input Validation**: All API inputs validated using Pydantic schemas
- **Error Sanitization**: Sensitive information filtered from error responses
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **CORS Configuration**: Configurable CORS settings for web clients

## 🧪 Testing

Run tests to ensure service reliability:

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=app tests/
```

## 📝 Logging

The service uses structured logging with different levels:

- **INFO**: General service operations
- **DEBUG**: Detailed processing information
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors and failures

Logs include:
- Request/response information
- Processing statistics
- Error details with stack traces
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the API documentation at `/rss/docs`
2. Review the service logs for error details
3. Open an issue in the repository
4. Contact the development team

## 🔄 Migration from Old Structure

The service has been completely restructured for better maintainability:

### Key Improvements

1. **Clean Architecture**: Proper separation of concerns
2. **Dependency Injection**: Better testability and modularity
3. **Type Safety**: Comprehensive type hints and validation
4. **Error Handling**: Robust error handling and recovery
5. **Documentation**: Auto-generated API documentation
6. **Monitoring**: Built-in health checks and statistics

### Migration Steps

1. Update environment variables to match new configuration
2. Update any external integrations to use new API endpoints
3. Review and update any custom configurations
4. Test thoroughly in staging environment
5. Deploy to production with proper monitoring

The new structure maintains backward compatibility while providing a much more robust and maintainable foundation for future development. 