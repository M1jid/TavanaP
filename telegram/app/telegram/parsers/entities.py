from telethon.tl.types import (
    User,
    Channel,
    Chat,
    PeerUser,
    PeerChannel,
    PeerChat,
    MessageEntityCustomEmoji,
    MessageEntityTextUrl,
    MessageEntityCode,
    MessageEntityUrl,
    MessageEntityBotCommand,
    MessageEntityHashtag,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityBold,
    MessageEntitySpoiler,
    MessageEntityEmail,
    MessageEntityPre,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityItalic,
)

REMOVE_TYPES = (
    MessageEntityBotCommand,  # Bot command
    MessageEntityCustomEmoji,  # Custom emoji
)

DUPLICATE_TYPES = (
    MessageEntityUrl,  # Url
    MessageEntityMention,  # Username mention
    MessageEntityMentionName,  # Mention name
    MessageEntityEmail,  # Email
    MessageEntityPre,  # Code section
)

KEEP_TYPES = (
    MessageEntityItalic,  # Italic
    MessageEntityTextUrl,  # Hyperlink
    MessageEntityHashtag,  # Hashtag
    MessageEntityBold,  # Bold
    MessageEntitySpoiler,  # Spoiler
    MessageEntityStrike,  # Strikethrough
    MessageEntityCode,  # Monospace
    MessageEntityBlockquote,  # Quate
)
