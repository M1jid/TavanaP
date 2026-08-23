# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.peer_channel import PeerChannelExtractor

import time

class GroupExtractor(PeerChannelExtractor):

    @staticmethod
    def get_type(obj):
        return 'GROUP'

    @staticmethod
    def extract(obj):
        return {
            "FETCH_TIME": int(time.time()),

            "TYPE": GroupExtractor.get_type(obj=obj),

            "ID": str(GroupExtractor.get_id(obj=obj)),
            "PEER_ID": GroupExtractor.get_id(obj=obj),
            "USERNAME": GroupExtractor.get_username(obj=obj),
            "TITLE": GroupExtractor.get_title(obj=obj),
            "DESCRIPTION": GroupExtractor.get_description(obj=obj),
            "URL": GroupExtractor.get_url(obj=obj),
            "FOLLOWERS": GroupExtractor.get_participants_count(obj=obj),

            "TAG": GroupExtractor.get_tag(obj=obj),
            
            "LINKED_CHANNEL_TITLE": GroupExtractor.get_linked_chat_title(obj=obj),
            "LINKED_CHANNEL_USERNAME": GroupExtractor.get_linked_chat_username(obj=obj),
            "LINKED_CHANNEL_ID": GroupExtractor.get_linked_chat_id(obj=obj),
            
            "AVAILABLE_REACTIONS": GroupExtractor.get_available_reactions(obj=obj),
            "CAN_VIEW_PARTICIPANTS": GroupExtractor.get_can_view_participants(obj=obj),
        }
