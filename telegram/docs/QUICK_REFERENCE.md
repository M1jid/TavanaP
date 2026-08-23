# Quick Reference Guide

A concise reference for the Telegram Data Collection Service.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)

## Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <repository-url>
cd services/telegram

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configure Accounts
```python
# Edit factory.py
accounts = [
    {
        "id": 1,
        "phone": "your_phone_number",
        "api_id": your_api_id,
        "api_hash": "your_api_hash",
        "session_file": "your_phone_number.session",
        "process": 0,
    }
]
```

### 3. Start Services
```bash
# Start with Docker Compose
docker-compose up -d

# Or run directly
python main.py
```

### 4. Verify Installation
```bash
# Check health
curl http://localhost:8000/health

# Check account status
curl http://localhost:8000/accounts/status
```

## Configuration

### Environment Variables
```bash
# Required
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=telegram

# Elasticsearch
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_INDEX_PREFIX=telegram

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/telegram_db
```

### Account Configuration
```python
accounts = [
    {
        "id": 1,                    # Unique account ID
        "phone": "1234567890",      # Phone number
        "api_id": 12345,           # Telegram API ID
        "api_hash": "hash",        # Telegram API Hash
        "session_file": "1234567890.session",  # Session file name
        "process": 0,              # Process ID (0 for main)
    }
]
```

## API Endpoints

### Health & Status
```bash
# Health check
GET /health

# Service status
GET /status

# Account status
GET /accounts/status
```

### Channel Management
```bash
# Join channel
POST /channels/join
{
    "channel_url": "https://t.me/example"
}

# List channels
GET /channels/list

# Leave channel
POST /channels/leave
{
    "channel_id": 123456789
}

# Get similar channels
POST /channels/similar
{
    "channel_id": 123456789,
    "min_participants": 300
}

# Handle small channels
POST /channels/handle-small
{
    "channel_id": 123456789
}
```

### Account Management
```bash
# Add account
POST /accounts/add
{
    "phone": "1234567890",
    "api_id": 12345,
    "api_hash": "hash"
}

# Remove account
DELETE /accounts/{account_id}

# Update account
PUT /accounts/{account_id}
{
    "phone": "new_phone",
    "api_id": 12345,
    "api_hash": "hash"
}
```

### Data Operations
```bash
# Sync channels
POST /sync/channels

# Process missing messages
POST /messages/process-missing

# Get message statistics
GET /messages/stats
```

## Common Commands

### Channel Discovery Commands
```bash
# Get similar channels for a specific channel
curl -X POST http://localhost:8000/channels/similar \
  -H "Content-Type: application/json" \
  -d '{"channel_id": 123456789, "min_participants": 300}'

# Handle small channels (leave if <100 participants)
curl -X POST http://localhost:8000/channels/handle-small \
  -H "Content-Type: application/json" \
  -d '{"channel_id": 123456789}'
```

### Docker Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f telegram-service

# Restart service
docker-compose restart telegram-service

# Scale service
docker-compose up -d --scale telegram-service=3
```

### Kubernetes Operations
```bash
# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods -n telegram-service

# View logs
kubectl logs -f deployment/telegram-service -n telegram-service

# Scale deployment
kubectl scale deployment telegram-service --replicas=3 -n telegram-service

# Port forward
kubectl port-forward service/telegram-service 8000:80 -n telegram-service
```

### Database Operations
```bash
# Connect to database
psql $DATABASE_URL

# Check tables
\dt telegram_*

# View channel data
SELECT * FROM telegram_peers LIMIT 10;

# Check account assignments
SELECT phone, COUNT(*) FROM telegram_peers GROUP BY phone;
```

### Elasticsearch Operations
```bash
# Check indices
curl -X GET "localhost:9200/_cat/indices?v"

# Search channels
curl -X GET "localhost:9200/telegram-channels/_search?q=title:news"

# Get document
curl -X GET "localhost:9200/telegram-channels/_doc/123456789"
```

### Redis Operations
```bash
# Connect to Redis
redis-cli

# List keys
keys *

# Get value
get key_name

# Clear all data
flushall
```

## Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Clear session files
rm *.session

# Restart service
docker-compose restart telegram-service
```

#### Rate Limiting
```bash
# Check flood wait errors
docker-compose logs telegram-service | grep FloodWait

# Service handles automatically, but you can increase delays
# Edit telegram_client.py and increase sleep times
```

#### Memory Issues
```bash
# Check memory usage
docker stats telegram-service

# Reduce batch size in configuration
BATCH_SIZE_TO_READ = 50  # Default is 100
```

#### Network Issues
```bash
# Test connectivity
curl -I https://api.telegram.org

# Check proxy settings
curl --proxy proxy_host:proxy_port https://api.telegram.org
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Or edit config
logging.basicConfig(level=logging.DEBUG)
```

### Emergency Procedures
```bash
# Stop all instances
docker-compose down
pkill -f telegram

# Clear corrupted data
rm *.session
rm -rf logs/*

# Restart with single instance
docker-compose up -d --scale telegram-service=1
```

## Monitoring

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Account status
curl http://localhost:8000/accounts/status
```

### Log Monitoring
```bash
# Follow logs
docker-compose logs -f telegram-service

# Filter by level
docker-compose logs telegram-service | grep ERROR
docker-compose logs telegram-service | grep WARNING

# Search for specific patterns
docker-compose logs telegram-service | grep "Authentication"
```

### Resource Monitoring
```bash
# Docker stats
docker stats telegram-service

# System resources
top -p $(pgrep -f telegram)

# Disk usage
df -h
du -sh sessions/ logs/
```

### Performance Metrics
```bash
# Message processing rate
curl http://localhost:8000/metrics | grep messages_processed

# Error rate
curl http://localhost:8000/metrics | grep errors_total

# Active accounts
curl http://localhost:8000/metrics | grep active_accounts
```

## Performance Tuning

### Batch Processing
```python
# Adjust batch size
BATCH_SIZE_TO_READ = 50  # Reduce for lower memory usage
BATCH_SIZE_TO_READ = 200  # Increase for higher throughput
```

### Concurrency
```python
# Adjust concurrent processing
MAX_CONCURRENT_PROCESSES = 5  # Default
MAX_CONCURRENT_PROCESSES = 10  # Higher concurrency
```

### Caching
```python
# Redis cache settings
REDIS_TTL = 3600  # Cache TTL in seconds
REDIS_MAX_MEMORY = "512mb"  # Max memory usage
```

### Database
```python
# Connection pool settings
DB_POOL_SIZE = 10  # Connection pool size
DB_MAX_OVERFLOW = 20  # Max overflow connections
```

## Security

### API Security
```bash
# Use HTTPS in production
# Set up authentication for API endpoints
# Rotate API keys regularly
```

### Session Security
```bash
# Encrypt session files
# Use secure storage for session files
# Regular session rotation
```

### Network Security
```bash
# Use VPN or private networks
# Implement firewall rules
# Use TLS for all communications
```

## Backup & Recovery

### Backup Commands
```bash
# Backup session files
tar -czf sessions_backup_$(date +%Y%m%d).tar.gz sessions/

# Backup database
pg_dump $DATABASE_URL > db_backup_$(date +%Y%m%d).sql

# Backup Elasticsearch
curl -X PUT "localhost:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)?wait_for_completion=true"
```

### Recovery Commands
```bash
# Restore session files
tar -xzf sessions_backup_YYYYMMDD.tar.gz

# Restore database
psql $DATABASE_URL < db_backup_YYYYMMDD.sql

# Restore Elasticsearch
curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_YYYYMMDD/_restore"
```

## Development

### Local Development
```bash
# Run in development mode
python main.py

# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Run tests
pytest

# Run linting
flake8
```

### Code Structure
```
services/telegram/
├── app/
│   ├── telegram/
│   │   ├── telegram_client.py    # Main client class
│   │   ├── account_manager.py    # Multi-account management
│   │   ├── extractors/           # Data extraction modules
│   │   └── decorators.py         # Retry decorators
│   ├── factory.py                # Application factory
│   └── config.py                 # Configuration
├── docs/                         # Documentation
├── main.py                       # Entry point
└── requirements.txt              # Dependencies
```

### Key Classes
- `TelegramClient`: Main client for Telegram operations
- `AccountManager`: Manages multiple Telegram accounts
- `ChannelExtractor`: Extracts channel data
- `MessageExtractor`: Extracts message data
- `UserExtractor`: Extracts user data

### Key Methods
- `start_client()`: Initialize and authenticate client
- `handle_new_message()`: Process incoming messages
- `store_channel_details()`: Store channel information
- `process_missing_messages()`: Process missed messages
- `join_to_new_entity()`: Join new channels/groups
- `get_similar_channels()`: Discover and sync similar channels
- `handle_small_channel_leave()`: Leave channels with low participant counts

This quick reference provides the essential information needed to work with the Telegram Data Collection Service. For detailed information, refer to the full documentation in the `docs/` directory.
