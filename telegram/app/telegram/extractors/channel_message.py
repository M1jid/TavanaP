import time

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.message import MessageExtractor


class ChannelMessageExtractor(MessageExtractor):

    @staticmethod
    def get_message_type():
        return 'CHANNELPOST'

    @staticmethod
    def get_public_url(obj, source_channel_username):
        if not source_channel_username:
            return f"https://t.me/c/{ChannelMessageExtractor.get_peer_id(obj.peer_id)}/{MessageExtractor.get_message_id(obj=obj)}"
        return f"https://t.me/{source_channel_username}/{MessageExtractor.get_message_id(obj=obj)}"

    @staticmethod
    def extract(obj, peer_username):
        result = ChannelMessageExtractor.extract_entities(obj)
        result['MEDIA'] = ChannelMessageExtractor.get_media(obj)

        result['FETCH_TIME']          = int(time.time())
        result['DATE']                = ChannelMessageExtractor.get_date(obj)
        result['TYPE']                = ChannelMessageExtractor.get_message_type()

        result['AUTHOR_ID']           = ChannelMessageExtractor.get_author_id(obj.from_id)
        result['AUTHOR_TYPE']         = ChannelMessageExtractor.get_author_type(obj.from_id)

        result['PEER_ID']             = ChannelMessageExtractor.get_peer_id(obj.peer_id)
        result['PEER_TYPE']           = 'CHANNEL'

        result['PUBLIC_URL']          = ChannelMessageExtractor.get_public_url(obj, peer_username)
        result['PRIVATE_URL']         = ChannelMessageExtractor.get_private_url(obj)
        result['ID']                  = str(result['PRIVATE_URL'])

        result['MESSAGE_ID']          = ChannelMessageExtractor.get_message_id(obj)
        result['MESSAGE']             = ChannelMessageExtractor.get_message(obj)

        result['REPLY_PEER_TYPE']     = ChannelMessageExtractor.get_reply_peer_type(obj)
        result['REPLY_PEER_ID']       = ChannelMessageExtractor.get_reply_peer_id(obj)
        result['REPLY_LINK']          = ChannelMessageExtractor.get_reply_link(obj)

        result['FWD_PEER_TYPE']       = ChannelMessageExtractor.get_fwd_peer_type(obj)
        result['FWD_PEER_ID']         = ChannelMessageExtractor.get_fwd_peer_id(obj)
        result['FWD_LINK']            = ChannelMessageExtractor.get_fwd_link(obj)

        result['REACTIONS']           = ChannelMessageExtractor.get_reactions(obj)
        result['REPLIES_COUNT']       = ChannelMessageExtractor.get_replies_count(obj)
        result['REACTIONS_COUNT']     = ChannelMessageExtractor.get_reactions_count(obj)
        result['VIEWS_COUNT']         = ChannelMessageExtractor.get_views_count(obj)
        result['FORWARDS_COUNT']      = ChannelMessageExtractor.get_forwards_count(obj)

        # persian_message = None
        # if obj.message:
        #     persian_message = ChannelMessageExtractor.check_persian_character(message=obj.message)
        # if persian_message:
        #     result['TAGS'] = ChannelMessageExtractor.get_tags(message=obj.message)
        #     result['SENTIMENT'] = ChannelMessageExtractor.get_sentiment(message=obj.message)
        #     result['SENSE'] = ChannelMessageExtractor.get_sense(message=obj.message)
        # else:
        #     result['TAGS'] = None
        #     result['SENTIMENT'] = None
        #     result['SENSE'] = None
        result['TAGS'] = None
        result['SENTIMENT'] = None
        result['SENSE'] = None

        return result
