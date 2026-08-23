# Telegram Data Collection Service

A production-grade Telegram data collection and processing service that monitors channels and groups, extracts messages, and routes them through Kafka for real-time data processing.

## 🚀 Overview

This service provides a robust, scalable solution for collecting and processing Telegram data using multiple Telegram accounts. It supports:

- **Multi-account management** with automatic session handling
- **Real-time message monitoring** from channels and groups
- **Message extraction and processing** with media support
- **Kafka integration** for message routing and distribution
- **Elasticsearch storage** for data persistence
- **MinIO integration** for media file storage
- **Redis caching** for performance optimization
- **Automatic channel joining** and management
- **Discussion group monitoring** for channel comments

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

The service follows a modular architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  AccountManager │    │ TelegramClient  │
│   (REST API)    │◄──►│  (Multi-Account)│◄──►│  (Core Logic)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kafka Router  │    │  ElasticSearch  │    │     MinIO       │
│  (Message Bus)  │    │   (Storage)     │    │  (Media Files)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   KSQL Streams  │    │     Redis       │    │   Extractors    │
│  (Processing)   │    │   (Caching)     │    │  (Data Parsing) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **TelegramClient**: Main client class handling Telegram API interactions
2. **AccountManager**: Manages multiple Telegram accounts and their sessions
3. **Extractors**: Parse and extract structured data from Telegram entities
4. **KafkaRouter**: Routes messages to appropriate Kafka topics
5. **Storage Handlers**: Manage data persistence across different backends

## ✨ Features

### 🔐 Multi-Account Management
- Support for multiple Telegram accounts with automatic session management
- Account rotation and load balancing
- Automatic session recovery and error handling

### 📡 Real-time Monitoring
- Live message monitoring from channels and groups
- Automatic channel joining and management
- Discussion group monitoring for channel comments
- Message forwarding and routing capabilities

### 📊 Data Processing
- Structured data extraction from messages, channels, and users
- Media file handling and storage
- Message categorization and tagging
- Comment and reply processing

### 🔄 Message Routing
- Kafka-based message distribution
- Configurable routing rules
- Message transformation and enrichment
- Real-time streaming capabilities

### 💾 Data Storage
- Elasticsearch for document storage and search
- MinIO for media file storage
- Redis for caching and session management
- PostgreSQL for metadata storage

### 🛡️ Error Handling & Resilience
- Automatic retry mechanisms with exponential backoff
- Proxy error handling and recovery
- Flood wait protection
- Graceful degradation

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Telegram API credentials
- Kafka cluster
- Elasticsearch cluster
- MinIO instance
- Redis instance

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd services/telegram
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Configure Telegram API credentials**
```bash
# Add your Telegram API credentials to the configuration
# You'll need api_id and api_hash from https://my.telegram.org
```

## ⚙️ Configuration

### Environment Variables

```bash
# Telegram API Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=telegram

# Elasticsearch Configuration
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_INDEX_PREFIX=telegram

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/telegram_db
```

### Account Configuration

Configure Telegram accounts in the `factory.py` file:

```python
accounts = [
    {
        "id": 1,
        "phone": "1234567890",
        "api_id": 12345,
        "api_hash": "your_api_hash",
        "session_file": "1234567890.session",
        "process": 0,
    }
]
```

## 🚀 Usage

### Starting the Service

1. **Development mode**
```bash
python main.py
```

2. **Production mode with Docker**
```bash
docker-compose up -d
```

3. **Using the API**
```bash
# Health check
curl http://localhost:8000/health

# Get account status
curl http://localhost:8000/accounts/status

# Join a channel
curl -X POST http://localhost:8000/channels/join \
  -H "Content-Type: application/json" \
  -d '{"channel_url": "https://t.me/example"}'
```

### API Endpoints

The service exposes a REST API for management and monitoring:

- `GET /health` - Service health check
- `GET /accounts/status` - Get all account statuses
- `POST /channels/join` - Join a new channel
- `GET /channels/list` - List monitored channels
- `POST /accounts/add` - Add a new Telegram account

## 📚 API Reference

### TelegramClient Class

The main client class for Telegram operations.

#### Constructor

```python
TelegramClient(
    api_id: str,
    api_hash: str,
    phone: str,
    session_path: str,
    proxy_server: tuple,
    ksql_handler: KsqlDBHandler,
    kafka_router: KafkaRouter,
    elastic_handler: ElasticHandler,
    minio_handler: MinIOHandler,
    channels_to_analyze: list,
    redis_handler: RedisHandler,
)
```

#### Key Methods

##### Authentication & Connection

```python
async def start_client(self)
```
Starts the Telegram client and authenticates the session.

```python
def free_channels(self)
```
Releases channels assigned to this account when errors occur.

##### Entity Management

```python
async def fetch_entity_by_link(self, link: str)
```
Fetches a Telegram entity (channel/group/user) by its link.

```python
async def fetch_entity_by_id(self, target_id: int)
```
Fetches a Telegram entity by its ID.

```python
async def fetch_full_channel(self, entity)
```
Fetches complete channel information including metadata.

##### Channel Operations

```python
async def join_to_public(self, link: str)
```
Joins a public channel using its invite link.

```python
async def join_to_private(self, invite_link: str)
```
Joins a private channel using its invite link.

```python
async def left_from_channel(self, channel_id: int)
```
Leaves a channel.

##### Data Storage

```python
async def store_channel_details(self, entity_id: int, channel_full=None, entity=None)
```
Stores channel information to Elasticsearch and KSQL.

```python
async def store_group_details(self, entity_id: int, channel_full=None, entity=None)
```
Stores group information to Elasticsearch and KSQL.

```python
async def store_user_details(self, user_id: int)
```
Stores user information to Elasticsearch and KSQL.

##### Message Processing

```python
async def handle_new_message(self, event)
```
Handles incoming new messages from monitored channels/groups.

```python
async def process_missing_messages(self)
```
Processes messages that were missed during downtime.

```python
async def update_messages(self, chat_id: int, entity, BATCH_SIZE_TO_READ: int = 100)
```
Updates messages for a specific chat.

##### Media Handling

```python
async def download_profile_photo(self, entity, channel_id: int, bucket_name: str = None)
```
Downloads and stores profile photos to MinIO.

##### Channel Discovery

```python
async def get_similar_channels(self, entity, MIN_NUMBERS: int = 300)
```
Discovers and syncs similar channels based on recommendations from a given entity.

**Parameters:**
- `entity`: Telegram channel entity to get recommendations for
- `MIN_NUMBERS`: Minimum participant count threshold (default: 300)

**Behavior:**
- Fetches channel recommendations from Telegram
- Filters channels by username and participant count
- Automatically syncs qualifying channels to database
- Skips channels with insufficient participants

##### Channel Management

```python
async def handle_small_channel_leave(self, entity)
```
Automatically leaves channels with low participant counts and marks them as blocked.

**Parameters:**
- `entity`: Telegram channel entity to evaluate

**Behavior:**
- Checks if channel has ≤100 participants
- Leaves channel if criteria met
- Updates database to mark channel as blocked
- Returns True if channel was left, False otherwise

##### Entity Mapping (Refactor)

```python
async def _ensure_entity_mapping(self, entity, last_message_id=None, unread_count=None, full_channel=None, on_startup=False)
```
Idempotent helper used by `add_entity_mappings`, `initialize_entity_mappings`, and `refresh_entity_mappings` to unify mapping logic for both channels and groups. It:

- Computes latest message and missed ranges
- Updates in-memory maps (`*_id_to_top_message`, `*_missed_range`, `chat_id_history`, etc.)
- Fetches and stores full entity details when needed
- Maintains linked channel/group relationships and Redis caches
- Syncs metadata to the database via `sync_entity_to_database`

### AccountManager Class

Manages multiple Telegram accounts and their lifecycle.

#### Key Methods

```python
async def initialize_accounts(self)
```
Initializes all configured Telegram accounts.

```python
async def on_update_messages(self)
```
Updates messages for all accounts.

```python
async def on_join_new_channels(self)
```
Joins new channels for all accounts.

```python
async def sync_channels(self)
```
Synchronizes channel information across all accounts.

## 🐳 Deployment

### Docker Deployment

1. **Build the image**
```bash
docker build -t telegram-service .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: telegram-service
  template:
    metadata:
      labels:
        app: telegram-service
    spec:
      containers:
      - name: telegram-service
        image: telegram-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: TELEGRAM_API_ID
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: api-id
        - name: TELEGRAM_API_HASH
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: api-hash
```

### Production Considerations

- **Resource Limits**: Set appropriate CPU and memory limits
- **Health Checks**: Configure liveness and readiness probes
- **Logging**: Use structured logging with proper log levels
- **Monitoring**: Set up metrics collection and alerting
- **Backup**: Regular backup of session files and configuration

## 📊 Monitoring

### Health Checks

The service provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Metrics

Key metrics to monitor:

- **Message Processing Rate**: Messages processed per second
- **Account Status**: Active/inactive accounts
- **Channel Count**: Number of monitored channels
- **Error Rate**: Failed operations per minute
- **Memory Usage**: RAM consumption
- **API Rate Limits**: Telegram API usage

### Logging

The service uses structured logging with the following levels:

- **INFO**: Normal operations and status updates
- **WARNING**: Non-critical issues and recoverable errors
- **ERROR**: Critical errors requiring attention
- **DEBUG**: Detailed debugging information

### Alerting

Set up alerts for:

- Account authentication failures
- High error rates
- Service unavailability
- Resource exhaustion
- Message processing delays

## 🔧 Troubleshooting

### Common Issues

#### Authentication Errors

**Problem**: `PhoneNumberBannedError` or `AuthKeyDuplicatedError`

**Solution**:
1. Check if the phone number is banned
2. Clear session files and re-authenticate
3. Use a different phone number

```bash
# Clear session files
rm *.session
# Restart the service
```

#### Rate Limiting

**Problem**: `FloodWaitError`

**Solution**:
1. The service automatically handles flood wait errors
2. Increase delays between operations
3. Use more accounts to distribute load

#### Connection Issues

**Problem**: Network connectivity problems

**Solution**:
1. Check proxy configuration
2. Verify network connectivity
3. Check firewall settings

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

1. **Batch Size**: Adjust `BATCH_SIZE_TO_READ` for optimal performance
2. **Concurrency**: Configure appropriate number of accounts
3. **Caching**: Optimize Redis cache settings
4. **Database**: Tune database connection pools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8

# Run type checking
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Multi-account support
- Real-time message monitoring
- Kafka integration
- Elasticsearch storage

### Version 1.1.0
- Added discussion group monitoring
- Improved error handling
- Performance optimizations
- Enhanced logging

---

**Note**: This service interacts with Telegram's API and should be used in compliance with Telegram's Terms of Service and applicable laws and regulations.
