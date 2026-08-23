import time

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.message import MessageExtractor


class GroupMessageExtractor(MessageExtractor):

    @staticmethod
    def get_message_type():
        return 'GROUPMESSAGE'

    @staticmethod
    def get_public_url(obj, source_group_username):
        if not source_group_username:
            return f"https://t.me/c/{GroupMessageExtractor.get_peer_id(obj.peer_id)}/{MessageExtractor.get_message_id(obj=obj)}"
        return f"https://t.me/{source_group_username}/{MessageExtractor.get_message_id(obj=obj)}"

    @staticmethod
    def extract(obj, peer_username):
        result = GroupMessageExtractor.extract_entities(obj)
        result['MEDIA'] = GroupMessageExtractor.get_media(obj)

        result['FETCH_TIME']          = int(time.time())
        result['DATE']                = GroupMessageExtractor.get_date(obj)
        result['TYPE']                = GroupMessageExtractor.get_message_type()

        result['AUTHOR_ID']           = GroupMessageExtractor.get_author_id(obj.from_id)
        result['AUTHOR_TYPE']         = GroupMessageExtractor.get_author_type(obj.from_id)

        result['PEER_ID']             = GroupMessageExtractor.get_peer_id(obj.peer_id)
        result['PEER_TYPE']           = 'GROUP'

        result['PUBLIC_URL']          = GroupMessageExtractor.get_public_url(obj, peer_username)
        result['PRIVATE_URL']         = GroupMessageExtractor.get_private_url(obj)
        result['ID']                  = str(result['PRIVATE_URL'])

        result['MESSAGE_ID']          = GroupMessageExtractor.get_message_id(obj)
        result['MESSAGE']             = GroupMessageExtractor.get_message(obj)

        result['REPLY_PEER_TYPE']     = GroupMessageExtractor.get_reply_peer_type(obj)
        result['REPLY_PEER_ID']       = GroupMessageExtractor.get_reply_peer_id(obj)
        result['REPLY_LINK']          = GroupMessageExtractor.get_reply_link(obj)

        result['FWD_PEER_TYPE']       = GroupMessageExtractor.get_fwd_peer_type(obj)
        result['FWD_PEER_ID']         = GroupMessageExtractor.get_fwd_peer_id(obj)
        result['FWD_LINK']            = GroupMessageExtractor.get_fwd_link(obj)

        result['REACTIONS']           = GroupMessageExtractor.get_reactions(obj)
        result['REPLIES_COUNT']       = GroupMessageExtractor.get_replies_count(obj)
        result['REACTIONS_COUNT']     = GroupMessageExtractor.get_reactions_count(obj)
        result['VIEWS_COUNT']         = GroupMessageExtractor.get_views_count(obj)
        result['FORWARDS_COUNT']      = GroupMessageExtractor.get_forwards_count(obj)

        # persian_message = None
        # if obj.message:
        #     persian_message = GroupMessageExtractor.check_persian_character(message=obj.message)
        # if persian_message:
        #     result['TAGS'] = GroupMessageExtractor.get_tags(message=obj.message)
        #     result['SENTIMENT'] = GroupMessageExtractor.get_sentiment(message=obj.message)
        #     result['SENSE'] = GroupMessageExtractor.get_sense(message=obj.message)
        # else:
        #     result['TAGS'] = None
        #     result['SENTIMENT'] = None
        #     result['SENSE'] = None
        result['TAGS'] = None
        result['SENTIMENT'] = None
        result['SENSE'] = None
        return result
