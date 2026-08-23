# Telegram Client API Documentation

This document provides detailed API documentation for the Telegram Data Collection Service.

## Table of Contents

- [Authentication](#authentication)
- [Account Management](#account-management)
- [Channel Management](#channel-management)
- [Message Processing](#message-processing)
- [Data Storage](#data-storage)
- [Error Handling](#error-handling)

## Authentication

### TelegramClient Authentication

The `TelegramClient` class handles authentication with Telegram's API using phone numbers and session files.

#### Constructor Parameters

```python
TelegramClient(
    api_id: str,                    # Telegram API ID
    api_hash: str,                  # Telegram API Hash
    phone: str,                     # Phone number for authentication
    session_path: str,              # Path to session file
    proxy_server: tuple,            # Proxy configuration (host, port, username, password)
    ksql_handler: KsqlDBHandler,    # KSQL database handler
    kafka_router: KafkaRouter,      # Kafka message router
    elastic_handler: ElasticHandler, # Elasticsearch handler
    minio_handler: MinIOHandler,    # MinIO storage handler
    channels_to_analyze: list,      # List of channels to monitor
    redis_handler: RedisHandler,    # Redis cache handler
)
```

#### Authentication Methods

##### `start_client()`

Starts the Telegram client and authenticates the session.

```python
async def start_client(self) -> None
```

**Behavior:**
- Attempts to start the client with the provided phone number
- Retrieves active sessions
- Connects if not already authorized
- Logs authentication status

**Error Handling:**
- Handles various Telegram authentication errors
- Automatically frees channels on authentication failures
- Implements retry logic with exponential backoff

**Example:**
```python
client = TelegramClient(...)
await client.start_client()
```

##### `free_channels()`

Releases channels assigned to this account when authentication errors occur.

```python
def free_channels(self) -> None
```

**Behavior:**
- Retrieves channels assigned to this phone number
- Updates channel subscriber status to available (1)
- Called automatically on authentication failures

## Account Management

### AccountManager Class

The `AccountManager` class manages multiple Telegram accounts and their lifecycle.

#### Key Methods

##### `initialize_accounts()`

Initializes all configured Telegram accounts.

```python
async def initialize_accounts(self) -> None
```

**Behavior:**
- Creates TelegramClient instances for each account
- Starts all clients concurrently
- Initializes entity mappings
- Sets up message handlers

##### `on_update_messages()`

Updates messages for all accounts.

```python
async def on_update_messages(self) -> None
```

**Behavior:**
- Processes missing messages for all accounts
- Updates message history
- Handles rate limiting and errors

##### `on_join_new_channels()`

Joins new channels for all accounts.

```python
async def on_join_new_channels(self) -> None
```

**Behavior:**
- Attempts to join new channels from the database
- Handles both public and private channels
- Manages channel limits and errors

##### `sync_channels()`

Synchronizes channel information across all accounts.

```python
async def sync_channels(self) -> None
```

**Behavior:**
- Syncs channel data with the database
- Updates channel metadata
- Removes channels no longer accessible

## Channel Management

### Entity Operations

#### `fetch_entity_by_link(link)`

Fetches a Telegram entity by its link.

```python
async def fetch_entity_by_link(self, link: str) -> Optional[Entity]
```

**Parameters:**
- `link` (str): Telegram entity link (e.g., "https://t.me/channel")

**Returns:**
- `Entity` or `None`: Telegram entity object or None if not found

**Example:**
```python
entity = await client.fetch_entity_by_link("https://t.me/example_channel")
```

#### `fetch_entity_by_id(target_id)`

Fetches a Telegram entity by its ID.

```python
async def fetch_entity_by_id(self, target_id: int) -> Optional[Entity]
```

**Parameters:**
- `target_id` (int): Telegram entity ID

**Returns:**
- `Entity` or `None`: Telegram entity object or None if not found

**Error Handling:**
- Returns `None` for private/invalid channels
- Returns `None` for deactivated users

#### `fetch_full_channel(entity)`

Fetches complete channel information including metadata.

```python
async def fetch_full_channel(self, entity: Entity) -> FullChannel
```

**Parameters:**
- `entity` (Entity): Telegram channel entity

**Returns:**
- `FullChannel`: Complete channel information

### Channel Operations

#### `join_to_public(link)`

Joins a public channel using its invite link.

```python
async def join_to_public(self, link: str) -> Optional[Updates]
```

**Parameters:**
- `link` (str): Public channel invite link

**Returns:**
- `Updates` or `None`: Join result or None on failure

**Example:**
```python
result = await client.join_to_public("https://t.me/example_channel")
```

#### `join_to_private(invite_link)`

Joins a private channel using its invite link.

```python
async def join_to_private(self, invite_link: str) -> Optional[Updates]
```

**Parameters:**
- `invite_link` (str): Private channel invite link

**Returns:**
- `Updates` or `None`: Join result or None on failure

**Example:**
```python
result = await client.join_to_private("https://t.me/+abc123")
```

#### `left_from_channel(channel_id)`

Leaves a channel.

```python
async def left_from_channel(self, channel_id: int) -> None
```

**Parameters:**
- `channel_id` (int): Channel ID to leave

**Example:**
```python
await client.left_from_channel(123456789)
```

#### `join_to_new_entity(peer)`

Joins a new entity (channel or group) based on peer information.

```python
async def join_to_new_entity(self, peer: dict) -> None
```

**Parameters:**
- `peer` (dict): Peer information containing URL and metadata

**Behavior:**
- Handles both public and private channels
- Manages discussion groups
- Updates database with join results
- Handles various join errors

## Message Processing

### Message Handling

#### `handle_new_message(event)`

Handles incoming new messages from monitored channels/groups.

```python
async def handle_new_message(self, event: events.NewMessage.Event) -> None
```

**Parameters:**
- `event` (events.NewMessage.Event): New message event

**Behavior:**
- Processes message content and metadata
- Extracts media and entities
- Routes messages to appropriate handlers
- Updates message history
- Sends read acknowledgments

#### `process_missing_messages()`

Processes messages that were missed during downtime.

```python
async def process_missing_messages(self) -> None
```

**Behavior:**
- Processes missing channel messages
- Processes missing group messages
- Handles batch processing with rate limiting

#### `update_messages(chat_id, entity, BATCH_SIZE_TO_READ)`

Updates messages for a specific chat.

```python
async def update_messages(
    self, 
    chat_id: int, 
    entity: Entity, 
    BATCH_SIZE_TO_READ: int = 100
) -> None
```

**Parameters:**
- `chat_id` (int): Chat ID to update
- `entity` (Entity): Chat entity
- `BATCH_SIZE_TO_READ` (int): Number of messages to process per batch

### Message Processing Pipeline

#### `_process_messages(messages, username)`

Internal method for processing message batches.

```python
async def _process_messages(self, messages: Union[Message, List[Message]], username: str = None) -> None
```

**Parameters:**
- `messages` (Union[Message, List[Message]]): Message(s) to process
- `username` (str): Channel/group username

**Behavior:**
- Handles forwarded messages
- Processes replies and comments
- Extracts media content
- Routes messages to Kafka

#### `_process_message_batch(entity_id, start_message_id, end_message_id, username, entity, BATCH_SIZE_TO_READ)`

Processes messages in batches for efficient handling.

```python
async def _process_message_batch(
    self,
    entity_id: int,
    start_message_id: int,
    end_message_id: int,
    username: str,
    entity: Entity = None,
    BATCH_SIZE_TO_READ: int = 100
) -> None
```

**Parameters:**
- `entity_id` (int): Entity ID
- `start_message_id` (int): Starting message ID
- `end_message_id` (int): Ending message ID
- `username` (str): Entity username
- `entity` (Entity): Entity object
- `BATCH_SIZE_TO_READ` (int): Batch size

### Comment Processing

#### `_process_comments(discussion_message_id, chat_id, source_message_id, channel_username, group_username, comments_count)`

Processes comments from discussion groups.

```python
async def _process_comments(
    self, 
    discussion_message_id: int, 
    chat_id: int, 
    source_message_id: int, 
    channel_username: str, 
    group_username: str, 
    comments_count: int
) -> None
```

**Parameters:**
- `discussion_message_id` (int): Discussion message ID
- `chat_id` (int): Chat ID
- `source_message_id` (int): Source message ID
- `channel_username` (str): Channel username
- `group_username` (str): Group username
- `comments_count` (int): Number of comments to process

## Data Storage

### Channel Storage

#### `store_channel_details(entity_id, channel_full, entity)`

Stores channel information to Elasticsearch and KSQL.

```python
async def store_channel_details(
    self, 
    entity_id: int, 
    channel_full: FullChannel = None, 
    entity: Entity = None
) -> Tuple[FullChannel, Optional[dict]]
```

**Parameters:**
- `entity_id` (int): Channel entity ID
- `channel_full` (FullChannel): Full channel data
- `entity` (Entity): Channel entity

**Returns:**
- `Tuple[FullChannel, Optional[dict]]`: Full channel data and extracted data

**Behavior:**
- Checks for existing data in Elasticsearch
- Downloads profile photo to MinIO
- Extracts channel metadata
- Stores data to KSQL stream
- Syncs with database

#### `store_group_details(entity_id, channel_full, entity)`

Stores group information to Elasticsearch and KSQL.

```python
async def store_group_details(
    self, 
    entity_id: int, 
    channel_full: FullChannel = None, 
    entity: Entity = None
) -> Tuple[FullChannel, Optional[dict]]
```

**Parameters:**
- `entity_id` (int): Group entity ID
- `channel_full` (FullChannel): Full group data
- `entity` (Entity): Group entity

**Returns:**
- `Tuple[FullChannel, Optional[dict]]`: Full group data and extracted data

#### `store_user_details(user_id)`

Stores user information to Elasticsearch and KSQL.

```python
async def store_user_details(self, user_id: int) -> Optional[dict]
```

**Parameters:**
- `user_id` (int): User ID

**Returns:**
- `Optional[dict]`: Extracted user data or None

**Behavior:**
- Fetches full user information
- Downloads profile photo
- Extracts user metadata
- Stores to KSQL stream

### Media Handling

#### `download_profile_photo(entity, channel_id, bucket_name)`

Downloads and stores profile photos to MinIO.

```python
async def download_profile_photo(
    self, 
    entity: Entity, 
    channel_id: int, 
    bucket_name: str = None
) -> None
```

**Parameters:**
- `entity` (Entity): Entity with profile photo
- `channel_id` (int): Channel/User ID
- `bucket_name` (str): MinIO bucket name

**Behavior:**
- Downloads profile photo from Telegram
- Uploads to MinIO storage
- Cleans up temporary files
- Handles missing photos gracefully

#### `get_similar_channels(entity, MIN_NUMBERS)`

Discovers and syncs similar channels based on recommendations from a given entity.

```python
async def get_similar_channels(
    self, 
    entity: Entity, 
    MIN_NUMBERS: int = 300
) -> None
```

**Parameters:**
- `entity` (Entity): Telegram channel entity to get recommendations for
- `MIN_NUMBERS` (int): Minimum participant count threshold (default: 300)

**Behavior:**
- Fetches channel recommendations from Telegram using `GetChannelRecommendationsRequest`
- Iterates through recommended channels
- Filters channels by:
  - Must have a valid username (not None or 'None')
  - Must meet minimum participant count threshold
- Automatically syncs qualifying channels to database
- Logs warnings for channels that don't meet criteria

**Example:**
```python
# Get similar channels with default threshold (300 participants)
await client.get_similar_channels(channel_entity)

# Get similar channels with custom threshold (500 participants)
await client.get_similar_channels(channel_entity, MIN_NUMBERS=500)
```

**Error Handling:**
- Uses retry decorator for automatic retry on failures
- Gracefully handles channels without usernames
- Continues processing even if individual channels fail

#### `handle_small_channel_leave(entity)`

Automatically leaves channels with low participant counts and marks them as blocked.

```python
async def handle_small_channel_leave(
    self, 
    entity: Entity
) -> bool
```

**Parameters:**
- `entity` (Entity): Telegram channel entity to evaluate

**Returns:**
- `bool`: True if channel was left, False otherwise

**Behavior:**
- Checks if channel has ≤100 participants
- If criteria met:
  - Logs the action
  - Leaves the channel using `left_from_channel()`
  - Updates database to mark channel as blocked with subscriber=2
  - Returns True
- If criteria not met:
  - Returns False without taking action

**Example:**
```python
# Check and potentially leave small channel
was_left = await client.handle_small_channel_leave(channel_entity)
if was_left:
    logger.info(f"Left small channel {channel_entity.id}")
```

**Error Handling:**
- Gracefully handles database update failures
- Returns False on any exception during database update
- Continues operation even if leaving fails

### Database Synchronization

#### `sync_channel_to_database(entity, linked_peer_id, _type, on_startup)`

Synchronizes channel information with the database.

```python
async def sync_channel_to_database(
    self, 
    entity: Entity, 
    linked_peer_id: int = None, 
    _type: bool = True, 
    on_startup: bool = False
) -> None
```

**Parameters:**
- `entity` (Entity): Channel/Group entity
- `linked_peer_id` (int): Linked peer ID
- `_type` (bool): True for channels, False for groups
- `on_startup` (bool): Whether called during startup

**Behavior:**
- Updates or creates channel records
- Manages subscriber assignments
- Handles linked channels/groups
- Updates metadata

### Entity Mapping

#### `_ensure_entity_mapping(entity, last_message_id, unread_count, full_channel, on_startup)`

Internal idempotent helper that ensures in-memory mappings and storage state are up to date for a given entity (channel or group).

```python
async def _ensure_entity_mapping(
    self,
    entity: Entity,
    last_message_id: Optional[int] = None,
    unread_count: Optional[int] = None,
    full_channel: Optional[FullChannel] = None,
    on_startup: bool = False,
) -> None
```

**Behavior:**
- Derives or fetches `last_message_id` and computes missed range
- Populates id-to-entity maps, sets top message, missed ranges, and `chat_id_history`
- Fetches full entity details and stores to KSQL/Elasticsearch if missing or stale
- Updates linked channel/group maps and Redis cache where applicable
- Calls `sync_entity_to_database` with correct flags

**Usage:**
- Used by `add_entity_mappings`, `initialize_entity_mappings`, and `refresh_entity_mappings` to centralize logic

#### `initialize_entity_mappings()` and `refresh_entity_mappings()`

Both methods now share the same internal flow by calling a common helper that iterates dialogs and invokes `_ensure_entity_mapping(..., on_startup=True)`. This reduces duplication and keeps behavior consistent and easy to understand.

## Error Handling

### Retry Decorator

All critical methods are decorated with `@retry_on_proxy_error_async` for automatic retry on failures.

```python
@retry_on_proxy_error_async(max_attempts=None, initial_delay=1, max_total_wait=None)
```

**Parameters:**
- `max_attempts` (int): Maximum retry attempts (None for unlimited)
- `initial_delay` (int): Initial delay in seconds
- `max_total_wait` (int): Maximum total wait time (None for unlimited)

### Common Error Types

#### Authentication Errors
- `PhoneNumberBannedError`: Phone number is banned
- `AuthKeyDuplicatedError`: Authentication key is duplicated
- `SessionRevokedError`: Session has been revoked
- `UserDeactivatedError`: User account is deactivated

#### Rate Limiting
- `FloodWaitError`: Rate limit exceeded, wait before retry
- `SlowModeWaitError`: Slow mode is active

#### Network Errors
- `ConnectionError`: Network connectivity issues
- `TimeoutError`: Request timeout
- `ProxyError`: Proxy connection issues

#### Channel Errors
- `ChannelPrivateError`: Channel is private
- `ChannelInvalidError`: Channel is invalid
- `InviteHashExpiredError`: Invite link has expired
- `UsernameNotOccupiedError`: Username doesn't exist

### Error Recovery Strategies

1. **Authentication Failures**: Free channels and retry with exponential backoff
2. **Rate Limiting**: Wait for specified duration before retry
3. **Network Issues**: Retry with increasing delays
4. **Channel Errors**: Mark channel as blocked and skip
5. **Session Issues**: Clear session and re-authenticate

### Logging

The service uses structured logging with different levels:

- **INFO**: Normal operations
- **WARNING**: Recoverable errors
- **ERROR**: Critical errors requiring attention
- **DEBUG**: Detailed debugging information

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing message from channel {channel_id}")
logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds")
logger.error(f"Authentication failed for account {phone}")
```

## Performance Considerations

### Batch Processing
- Messages are processed in configurable batches
- Default batch size: 100 messages
- Adjustable based on system resources

### Rate Limiting
- Built-in flood wait handling
- Automatic delays between operations
- Configurable retry strategies

### Caching
- Redis caching for frequently accessed data
- Session persistence across restarts
- Entity mapping optimization

### Resource Management
- Automatic cleanup of temporary files
- Memory-efficient message processing
- Connection pooling for external services

