# Troubleshooting Guide

This guide provides solutions for common issues encountered when running the Telegram Data Collection Service.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Connection Problems](#connection-problems)
- [Rate Limiting](#rate-limiting)
- [Data Processing Issues](#data-processing-issues)
- [Performance Problems](#performance-problems)
- [Storage Issues](#storage-issues)
- [Monitoring and Debugging](#monitoring-and-debugging)
- [Emergency Procedures](#emergency-procedures)

## Authentication Issues

### Phone Number Banned

**Symptoms:**
- `PhoneNumberBannedError` in logs
- Service fails to start
- Authentication repeatedly fails

**Solutions:**

1. **Check if phone number is actually banned**
```bash
# Try to log in manually to Telegram
# If you can't log in, the number is banned
```

2. **Use a different phone number**
```python
# Update account configuration in factory.py
accounts = [
    {
        "id": 1,
        "phone": "new_phone_number",  # Replace with new number
        "api_id": 12345,
        "api_hash": "your_api_hash",
        "session_file": "new_phone_number.session",
        "process": 0,
    }
]
```

3. **Clear session files and re-authenticate**
```bash
# Remove old session files
rm *.session

# Restart the service
docker-compose restart telegram-service
```

### Auth Key Duplicated

**Symptoms:**
- `AuthKeyDuplicatedError` in logs
- Multiple instances trying to use same session

**Solutions:**

1. **Stop all instances**
```bash
# Stop all running containers
docker-compose down

# Kill any remaining processes
pkill -f telegram
```

2. **Clear session files**
```bash
rm *.session
```

3. **Restart with single instance**
```bash
docker-compose up -d
```

### Session Revoked

**Symptoms:**
- `SessionRevokedError` in logs
- Service can't authenticate

**Solutions:**

1. **Clear session and re-authenticate**
```bash
rm *.session
docker-compose restart telegram-service
```

2. **Check for security alerts**
- Check Telegram app for security alerts
- Verify account hasn't been compromised

### User Deactivated

**Symptoms:**
- `UserDeactivatedError` or `UserDeactivatedBanError`
- Account no longer accessible

**Solutions:**

1. **Check account status**
```bash
# Try to log in manually to Telegram
# Check if account is deactivated
```

2. **Replace with new account**
```python
# Update account configuration
accounts = [
    {
        "id": 1,
        "phone": "new_phone_number",
        "api_id": 12345,
        "api_hash": "your_api_hash",
        "session_file": "new_phone_number.session",
        "process": 0,
    }
]
```

## Connection Problems

### Network Connectivity Issues

**Symptoms:**
- Connection timeouts
- Service can't reach Telegram servers
- Proxy errors

**Solutions:**

1. **Check network connectivity**
```bash
# Test basic connectivity
ping api.telegram.org

# Test with curl
curl -I https://api.telegram.org
```

2. **Verify proxy configuration**
```python
# Check proxy settings in config
proxy_server = ('proxy_host', proxy_port, 'username', 'password')
```

3. **Test proxy connectivity**
```bash
# Test proxy with curl
curl --proxy proxy_host:proxy_port https://api.telegram.org
```

### DNS Resolution Issues

**Symptoms:**
- Can't resolve Telegram domains
- Connection timeouts

**Solutions:**

1. **Check DNS resolution**
```bash
nslookup api.telegram.org
nslookup core.telegram.org
```

2. **Update DNS servers**
```bash
# Add to /etc/resolv.conf
nameserver 8.8.8.8
nameserver 1.1.1.1
```

3. **Use IP addresses directly**
```python
# In extreme cases, use IP addresses
# This is not recommended for production
```

### Firewall Issues

**Symptoms:**
- Connection blocked
- Port access denied

**Solutions:**

1. **Check firewall rules**
```bash
# Check if ports are blocked
sudo ufw status
sudo iptables -L
```

2. **Allow required ports**
```bash
# Allow outbound connections
sudo ufw allow out 443/tcp
sudo ufw allow out 80/tcp
```

## Rate Limiting

### Flood Wait Errors

**Symptoms:**
- `FloodWaitError` in logs
- Service stops processing messages
- Long delays between operations

**Solutions:**

1. **The service automatically handles flood wait**
```python
# Built-in retry mechanism handles this
@retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
```

2. **Increase delays between operations**
```python
# Add more delays in processing loops
await asyncio.sleep(5)  # Increase from 3 to 5 seconds
```

3. **Use more accounts to distribute load**
```python
# Add more accounts to spread the load
accounts = [
    # ... existing accounts
    {
        "id": 3,
        "phone": "additional_phone",
        "api_id": 12345,
        "api_hash": "your_api_hash",
        "session_file": "additional_phone.session",
        "process": 0,
    }
]
```

### Slow Mode Errors

**Symptoms:**
- `SlowModeWaitError` in logs
- Messages sent too frequently

**Solutions:**

1. **Increase delays between messages**
```python
# Add longer delays
await asyncio.sleep(10)  # Wait 10 seconds between messages
```

2. **Implement message queuing**
```python
# Queue messages and send with delays
import asyncio
from collections import deque

message_queue = deque()

async def send_messages_with_delay():
    while message_queue:
        message = message_queue.popleft()
        await send_message(message)
        await asyncio.sleep(5)  # 5 second delay
```

## Data Processing Issues

### Message Processing Failures

**Symptoms:**
- Messages not being processed
- Errors in message extraction
- Missing data in storage

**Solutions:**

1. **Check message processing logs**
```bash
# Check for processing errors
docker-compose logs telegram-service | grep -i error
```

2. **Verify extractor configuration**
```python
# Check if extractors are properly configured
from app.telegram.extractors.channel import ChannelExtractor
from app.telegram.extractors.message import MessageExtractor
```

3. **Test message extraction manually**
```python
# Test extraction with sample data
sample_message = {...}  # Sample message data
extracted = MessageExtractor.extract(sample_message)
print(extracted)
```

### Media Processing Issues

**Symptoms:**
- Media files not downloaded
- Profile photos missing
- MinIO upload failures

**Solutions:**

1. **Check MinIO connectivity**
```bash
# Test MinIO connection
curl -I http://minio:9000
```

2. **Verify MinIO credentials**
```python
# Check MinIO configuration
minio_handler = MinIOHandler(
    endpoint="minio:9000",
    access_key="your_access_key",
    secret_key="your_secret_key"
)
```

3. **Check disk space**
```bash
# Check available disk space
df -h
```

### Database Synchronization Issues

**Symptoms:**
- Data not syncing to database
- Duplicate records
- Missing channel information

**Solutions:**

1. **Check database connectivity**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"
```

2. **Verify database schema**
```sql
-- Check if tables exist
\dt telegram_*

-- Check table structure
\d telegram_peers
```

3. **Check for constraint violations**
```sql
-- Check for duplicate entries
SELECT peer_id, COUNT(*) FROM telegram_peers GROUP BY peer_id HAVING COUNT(*) > 1;
```

## Performance Problems

### High Memory Usage

**Symptoms:**
- Service using excessive memory
- Out of memory errors
- Slow performance

**Solutions:**

1. **Monitor memory usage**
```bash
# Check memory usage
docker stats telegram-service

# Check memory usage in Kubernetes
kubectl top pods -n telegram-service
```

2. **Optimize batch processing**
```python
# Reduce batch size
BATCH_SIZE_TO_READ = 50  # Reduce from 100 to 50
```

3. **Implement memory cleanup**
```python
# Add explicit garbage collection
import gc

async def process_messages_with_cleanup():
    # Process messages
    await process_messages()
    
    # Clean up memory
    gc.collect()
```

### High CPU Usage

**Symptoms:**
- Service consuming excessive CPU
- Slow response times
- System overload

**Solutions:**

1. **Monitor CPU usage**
```bash
# Check CPU usage
top -p $(pgrep -f telegram)

# In Kubernetes
kubectl top pods -n telegram-service
```

2. **Optimize processing loops**
```python
# Add delays to reduce CPU usage
await asyncio.sleep(1)  # Add 1 second delay
```

3. **Use async processing**
```python
# Process messages asynchronously
async def process_messages_async(messages):
    tasks = [process_single_message(msg) for msg in messages]
    await asyncio.gather(*tasks)
```

### Slow Message Processing

**Symptoms:**
- Messages taking long time to process
- Backlog of unprocessed messages
- Delayed data availability

**Solutions:**

1. **Increase concurrency**
```python
# Process multiple messages concurrently
async def process_message_batch(messages):
    semaphore = asyncio.Semaphore(10)  # Limit concurrent processing
    
    async def process_with_semaphore(message):
        async with semaphore:
            return await process_message(message)
    
    tasks = [process_with_semaphore(msg) for msg in messages]
    return await asyncio.gather(*tasks)
```

2. **Optimize database queries**
```python
# Use batch inserts
async def batch_insert_messages(messages):
    # Group messages for batch insert
    batch_data = [extract_message_data(msg) for msg in messages]
    await database.batch_insert(batch_data)
```

3. **Use caching**
```python
# Cache frequently accessed data
@lru_cache(maxsize=1000)
def get_cached_entity(entity_id):
    return fetch_entity(entity_id)
```

## Storage Issues

### Elasticsearch Issues

**Symptoms:**
- Data not stored in Elasticsearch
- Search queries failing
- Index errors

**Solutions:**

1. **Check Elasticsearch health**
```bash
# Check cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Check indices
curl -X GET "localhost:9200/_cat/indices?v"
```

2. **Verify index mapping**
```bash
# Check index mapping
curl -X GET "localhost:9200/telegram-channels/_mapping?pretty"
```

3. **Recreate corrupted indices**
```bash
# Delete and recreate index
curl -X DELETE "localhost:9200/telegram-channels"
# Service will recreate index on next run
```

### MinIO Issues

**Symptoms:**
- Media files not uploaded
- Storage errors
- Missing files

**Solutions:**

1. **Check MinIO status**
```bash
# Check MinIO health
curl -I http://minio:9000/minio/health/live
```

2. **Verify bucket existence**
```bash
# List buckets
mc ls minio/

# Create bucket if missing
mc mb minio/telegram-images-channels
mc mb minio/telegram-images-groups
mc mb minio/telegram-images-users
```

3. **Check permissions**
```bash
# Verify access permissions
mc policy list minio/telegram-images-channels
```

### Redis Issues

**Symptoms:**
- Cache misses
- Session data lost
- Performance degradation

**Solutions:**

1. **Check Redis connectivity**
```bash
# Test Redis connection
redis-cli ping

# Check Redis info
redis-cli info
```

2. **Monitor Redis memory**
```bash
# Check memory usage
redis-cli info memory

# Check keys
redis-cli keys "*"
```

3. **Clear corrupted data**
```bash
# Clear all data (use with caution)
redis-cli flushall

# Clear specific keys
redis-cli del key_name
```

## Monitoring and Debugging

### Enable Debug Logging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in environment
export LOG_LEVEL=DEBUG
```

### Check Service Health

```bash
# Check service health endpoint
curl http://localhost:8000/health

# Check detailed status
curl http://localhost:8000/status
```

### Monitor Logs

```bash
# Follow logs in real-time
docker-compose logs -f telegram-service

# Filter logs by level
docker-compose logs telegram-service | grep ERROR

# In Kubernetes
kubectl logs -f deployment/telegram-service -n telegram-service
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats telegram-service

# Check network connections
netstat -tulpn | grep telegram

# Monitor disk I/O
iotop -p $(pgrep -f telegram)
```

### Debug Specific Issues

1. **Authentication Debugging**
```python
# Add debug logging to authentication
logger.debug(f"Attempting to authenticate with phone: {self.phone}")
logger.debug(f"Session path: {self.session_path}")
```

2. **Message Processing Debugging**
```python
# Add debug logging to message processing
logger.debug(f"Processing message: {message.id}")
logger.debug(f"Message content: {message.text[:100]}...")
```

3. **Database Debugging**
```python
# Add debug logging to database operations
logger.debug(f"Storing channel: {entity_id}")
logger.debug(f"Channel data: {channel_data}")
```

## Emergency Procedures

### Service Recovery

1. **Stop all instances**
```bash
# Stop all containers
docker-compose down

# Kill any remaining processes
pkill -f telegram
```

2. **Clear corrupted data**
```bash
# Clear session files
rm *.session

# Clear logs
rm -rf logs/*

# Clear temporary files
rm -rf /tmp/telegram_*
```

3. **Restart with single instance**
```bash
# Start with single instance
docker-compose up -d --scale telegram-service=1
```

### Data Recovery

1. **Restore from backup**
```bash
# Restore session files
tar -xzf sessions_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore database
gunzip db_backup_YYYYMMDD_HHMMSS.sql.gz
psql $DATABASE_URL < db_backup_YYYYMMDD_HHMMSS.sql
```

2. **Re-sync data**
```bash
# Trigger data re-sync
curl -X POST http://localhost:8000/sync/channels
```

### Emergency Contact

For critical issues that cannot be resolved with this guide:

1. **Check system resources**
```bash
# Check system status
top
df -h
free -h
```

2. **Collect diagnostic information**
```bash
# Collect logs
docker-compose logs telegram-service > telegram_logs.txt

# Collect system info
uname -a > system_info.txt
df -h > disk_usage.txt
```

3. **Contact support team**
- Provide diagnostic information
- Include error logs
- Describe the issue and steps taken

### Preventive Measures

1. **Regular monitoring**
```bash
# Set up monitoring scripts
#!/bin/bash
# Check service health every 5 minutes
while true; do
    if ! curl -f http://localhost:8000/health; then
        echo "Service down at $(date)" >> health_check.log
        # Send alert
    fi
    sleep 300
done
```

2. **Automated backups**
```bash
# Set up automated backups
#!/bin/bash
# Daily backup script
tar -czf sessions_backup_$(date +%Y%m%d).tar.gz sessions/
pg_dump $DATABASE_URL > db_backup_$(date +%Y%m%d).sql
```

3. **Resource monitoring**
```bash
# Monitor resource usage
#!/bin/bash
# Check memory usage
memory_usage=$(docker stats --no-stream --format "table {{.MemUsage}}" telegram-service)
echo "$(date): $memory_usage" >> resource_monitor.log
```

This troubleshooting guide should help resolve most common issues. For persistent problems, consult the logs and consider reaching out to the development team with detailed diagnostic information.
