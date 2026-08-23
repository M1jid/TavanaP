## POST `/fa/channelspost`

**Summary**: Get Telegram channel posts.

**Request Body**: `TelegramChannelsFilter`  
*(same as above)*

**Response**: `List[TelegramMessage]`

Returns a list of channel posts matching the filters.

---

## Model: TelegramMessage

All fields are optional. Fields may be `null`.

| Field                     | Type               | Description                             |
|--------------------------|--------------------|-----------------------------------------|
| AUTHOR_ID                | `int`              | ID of the message author                |
| SPOILER_PARTS            | `List[str]`        | Parts of message marked as spoilers     |
| PEER_TYPE                | `str`              | Type of the chat/channel                |
| LINKS                    | `List[str]`        | Extracted links in the message          |
| SENTIMENT                | `str`              | Sentiment analysis result               |
| MESSAGE                  | `str`              | Raw message text                        |
| CODES                    | `List[str]`        | Code blocks in the message              |
| FORWARDS_COUNT           | `int`              | Number of times forwarded               |
| MESSAGE_ID               | `int`              | Unique message ID                       |
| PRIVATE_URL              | `str`              | URL for private access to the message   |
| MEDIA                    | `List[str]`        | Media items (e.g., images, videos)      |
| TYPE                     | `str`              | Type of message (`CHANNELPOST`, etc.)   |
| FWD_LINK                 | `str`              | Forward link                            |
| REPLY_LINK               | `str`              | Reply link                              |
| REACTIONS                | `Dict[str, int]`   | Reactions and their counts              |
| MONOSPACE_PARTS          | `List[str]`        | Monospaced text parts (e.g., code)      |
| REACTIONS_COUNT          | `int`              | Total number of reactions               |
| BLOCKQUOTE_PARTS         | `List[str]`        | Blockquote sections                     |
| VIEWS_COUNT              | `int`              | Number of views                         |
| MENTIONS                 | `List[str]`        | Mentions in the message                 |
| CLEANED_MESSAGE          | `str`              | Preprocessed version of the message     |
| HASHTAGS                 | `List[str]`        | Hashtags in the message                 |
| FWD_PEER_TYPE            | `str`              | Type of peer from which message was forwarded |
| DATE                     | `str`              | Date and time of the message (ISO 8601) |
| REPLY_PEER_TYPE          | `str`              | Type of peer replied to                 |
| REPLIES_COUNT            | `int`              | Number of replies                       |
| FWD_PEER_ID              | `int`              | ID of the peer from which it was forwarded |
| BOLDED_PARTS             | `List[str]`        | Bolded parts of the message             |
| AUTHOR_TYPE              | `str`              | Type of the author                      |
| STRIKETHROUGHED_PARTS    | `List[str]`        | Strikethrough parts                     |
| FETCH_TIME               | `int`              | Timestamp of data fetch (Unix)          |
| PUBLIC_URL               | `str`              | Public URL to view the message          |
| PEER_ID                  | `int`              | ID of the originating channel/chat      |
| SENSE                    | `str`              | Semantic classification                 |
| REPLY_PEER_ID            | `int`              | Peer ID that is being replied to        |
| TAGS                     | `List[str]`        | Custom tags assigned                    |

---

## Authentication

All endpoints require an authenticated user with the appropriate permission:

- `/fa/channelspost` → `platform.telegram.fa.channelpost`
