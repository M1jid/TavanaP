# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.peer_channel import PeerChannelExtractor

import time

class ChannelExtractor(PeerChannelExtractor):

    @staticmethod
    def get_type(obj):
        return 'CHANNEL'

    @staticmethod
    def extract(obj):
        return {
            "FETCH_TIME": int(time.time()),

            "TYPE": ChannelExtractor.get_type(obj=obj),

            "ID": str(ChannelExtractor.get_id(obj=obj)),
            "PEER_ID": ChannelExtractor.get_id(obj=obj),
            "USERNAME": ChannelExtractor.get_username(obj=obj),
            "TITLE": ChannelExtractor.get_title(obj=obj),
            "DESCRIPTION": ChannelExtractor.get_description(obj=obj),
            "URL": ChannelExtractor.get_url(obj=obj),
            "FOLLOWERS": ChannelExtractor.get_participants_count(obj=obj),

            "TAG": ChannelExtractor.get_tag(obj=obj),

            "LINKED_GROUP_TITLE": ChannelExtractor.get_linked_chat_title(obj=obj),
            "LINKED_GROUP_USERNAME": ChannelExtractor.get_linked_chat_username(obj=obj),
            "LINKED_GROUP_ID": ChannelExtractor.get_linked_chat_id(obj=obj),

            "AVAILABLE_REACTIONS": ChannelExtractor.get_available_reactions(obj=obj),
            "CAN_VIEW_PARTICIPANTS": ChannelExtractor.get_can_view_participants(obj=obj),
        }
