# All message document types. (see: https://core.telegram.org/type/MessageMedia)


from telethon.tl.types import (
    MessageMediaVenue,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaGeo,
    MessageMediaContact,
    MessageMediaWebPage,
    MessageMediaGame,
    MessageMediaInvoice,
    MessageMediaGeoLive,
    MessageMediaPoll,
    MessageMediaDice,
    MessageMediaStory,
    MessageMediaGiveaway,
    MessageMediaGiveawayResults,
    MessageMediaPaidMedia,
    MessageMediaEmpty,
    MessageMediaUnsupported,
)

MESSAGE_GEO = (
    MessageMediaVenue,
    MessageMediaGeo,
    MessageMediaGeoLive,
)

MESSAGE_GIFT = (
    MessageMediaGiveawayResults,
    MessageMediaGiveaway,
)

MESSAGE_PAYMENT = (
    MessageMediaPaidMedia,
    MessageMediaInvoice,
)

MESSAGE_NON_IMPORTANT_TYPES = (
    MessageMediaUnsupported,
    MessageMediaEmpty,
    MessageMediaDice,
    MessageMediaStory,
    MessageMediaContact,
    MessageMediaWebPage,
)

MESSAGE_MEDIAS = (
    MessageMediaPhoto,
    MessageMediaDocument,
)

MESSAGE_POOL = (
    MessageMediaPoll,
)

