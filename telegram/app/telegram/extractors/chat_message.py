from pickle import NONE
import time

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.message import MessageExtractor


class ChatMessageExtractor(MessageExtractor):

    @staticmethod
    def get_message_type():
        return 'CHATMESSAGE'
    
    @staticmethod
    def get_web_link(obj, username):
        if not username:
            return f'https://web.telegram.org/k/#{ChatMessageExtractor.get_peer_id(obj.peer_id)}/{MessageExtractor.get_message_id(obj=obj)}'
        else:
            f'https://web.telegram.org/k/#@{username}/{MessageExtractor.get_message_id(obj=obj)}'

    @staticmethod
    def get_url(obj, admin_id):
        return f"{admin_id}-{MessageExtractor.get_peer_id(peer_id=obj.peer_id)}-{MessageExtractor.get_message_id(obj=obj)}"

    @staticmethod
    def get_chat_reply_link(obj, admin_id):
        if not obj.reply_to or not obj.reply_to.reply_to_msg_id:
            return None
        return f"{admin_id}-{MessageExtractor.get_reply_peer_id(obj)}-{obj.reply_to.reply_to_msg_id}"

    @staticmethod
    def extract(obj, media_path, admin_id):
        result = ChatMessageExtractor.extract_entities(obj)

        result['MEDIA'] = media_path

        if obj.grouped_id:
            result['GROUPED_ID'] = str(obj.grouped_id)
        else:
            result['GROUPED_ID'] = None

        result['FETCH_TIME']          = int(time.time())
        result['DATE']                = ChatMessageExtractor.get_date(obj)
        result['EDIT_DATE']           = ChatMessageExtractor.get_edit_date(obj)
        result['TYPE']                = ChatMessageExtractor.get_message_type()
        result['OUT']                 = obj.out

        if obj.out:
            result['AUTHOR_ID']       = admin_id
        else:
            result['AUTHOR_ID']       = ChatMessageExtractor.get_peer_id(obj.peer_id)

        result['PEER_ID']             = ChatMessageExtractor.get_peer_id(obj.peer_id)
        result['PEER_TYPE']           = 'USER'

        result['URL']                 = ChatMessageExtractor.get_url(obj, admin_id=admin_id)
        result['ID']                  = result['URL']
        result['ADMIN_PEER_ID']       = admin_id
        result['MESSAGE_ID']          = ChatMessageExtractor.get_message_id(obj)
        result['MESSAGE']             = ChatMessageExtractor.get_message(obj)

        result['REPLY_PEER_TYPE']     = ChatMessageExtractor.get_reply_peer_type(obj)
        result['REPLY_PEER_ID']       = ChatMessageExtractor.get_reply_peer_id(obj)
        if result['REPLY_PEER_TYPE']  == 'USER':
            result['REPLY_LINK']      = ChatMessageExtractor.get_chat_reply_link(obj, admin_id)
        else:
            result['REPLY_LINK']      = ChatMessageExtractor.get_reply_link(obj)

        result['FWD_PEER_TYPE']       = ChatMessageExtractor.get_fwd_peer_type(obj)
        result['FWD_PEER_ID']         = ChatMessageExtractor.get_fwd_peer_id(obj)
        if result['FWD_PEER_TYPE']    == 'USER':
            result['FWD_LINK']        = None
        else:
            result['FWD_LINK']        = ChatMessageExtractor.get_fwd_link(obj)

        result['TEXT_REACTIONS']      = ChatMessageExtractor.get_text_reactions(obj)

        # persian_message = None
        # if obj.message:
        #     persian_message = ChatMessageExtractor.check_persian_character(message=obj.message)
        # if persian_message:
        #     result['TAGS'] = ChatMessageExtractor.get_tags(message=obj.message)
        #     result['SENTIMENT'] = ChatMessageExtractor.get_sentiment(message=obj.message)
        #     result['SENSE'] = ChatMessageExtractor.get_sense(message=obj.message)
        # else:
        #     result['TAGS'] = None
        #     result['SENTIMENT'] = None
        #     result['SENSE'] = None
        result['TAGS'] = None
        result['SENTIMENT'] = None
        result['SENSE'] = None
        return result
