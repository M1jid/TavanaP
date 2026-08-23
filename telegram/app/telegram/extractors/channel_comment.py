import time

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.telegram.extractors.message import MessageExtractor


class ChannelCommentExtractor(MessageExtractor):

    @staticmethod
    def get_message_type():
        return 'CHANNELCOMMENT'

    @staticmethod
    def get_public_url(obj, discussion_message_id, source_message_id, source_channel_username, source_group_username):

        """
            Constructs the public URL of a comment that replies to a post originally made in a channel
            (either public or private), and then forwarded to a linked discussion group
            (also either public or private).

            ────────────────────────────────────────────────────────────────
            CASE 1: Public Channel (with any type of discussion group)
            ────────────────────────────────────────────────────────────────

            Notes:
                - The final URL points to the **original public channel post**, with a `?comment=` query
                that links to the comment message in the discussion group.

            URL Format:
                https://t.me/{public_channel_username}/{channel_message_id}?comment={comment_message_id}

            Example 1 — Public discussion group:
                - Public channel username: ufiuwriuwifywufywuf
                - Original post: https://t.me/ufiuwriuwifywufywuf/48
                - Comment in discussion group: https://t.me/kjdbdkwbdkflwje/63
                - Resulting URL: https://t.me/ufiuwriuwifywufywuf/48?comment=63

            Example 2 — Private discussion group:
                - Public channel username: ugsbhdicysdcj
                - Original post: https://t.me/ugsbhdicysdcj/3
                - Comment in private group: https://t.me/c/2592767575/4
                - Resulting URL: https://t.me/ugsbhdicysdcj/3?comment=4

            ────────────────────────────────────────────────────────────────
            CASE 2: Private Channel → Public Discussion Group
            ────────────────────────────────────────────────────────────────

            Notes:
                - The original channel is private (its posts have `/c/{id}` links).
                - The discussion group is public (has a username).
                - The resulting URL uses the discussion group's public link with a `?thread=` query 
                pointing to the forwarded message.

            URL Format:
                https://t.me/{discussion_group_username}/{comment_message_id}?thread={forwarded_message_id}

            Example Scenario:
                - Private channel ID: 2613928314
                - Original post: https://t.me/c/2613928314/3

                - Message forwarded to discussion group:
                    - Discussion group username: skjdhvshdcdshbcb
                    - Forwarded message URL: https://t.me/skjdhvshdcdshbcb/12

                - Comment in the discussion group:
                    - Comment URL: https://t.me/skjdhvshdcdshbcb/15
                    - Resulting URL: https://t.me/skjdhvshdcdshbcb/15?thread=12

            ────────────────────────────────────────────────────────────────
            CASE 3: Private Channel → Private Discussion Group
            ────────────────────────────────────────────────────────────────

            Notes:
                - The resulting URL uses `/c/{group_id}` and includes a `?thread=` query 
                pointing to the forwarded message ID.

            URL Format:
                https://t.me/c/{discussion_group_id}/{comment_message_id}?thread={forwarded_message_id}

            Example Scenario:
                - Private channel ID: 2527223071
                - Original post: https://t.me/c/2527223071/20

                - Forwarded to private discussion group:
                    - Group ID: 2801452651
                    - Forwarded message URL: https://t.me/c/2801452651/25

                - Comment:
                    - Comment URL: https://t.me/c/2801452651/27
                    - Resulting URL: https://t.me/c/2801452651/27?thread=25
        """

        # Case 1
        if source_channel_username:
            return f'https://t.me/{source_channel_username}/{source_message_id}?comment={ChannelCommentExtractor.get_message_id(obj)}'

        # Case 2
        if not source_channel_username and source_group_username:
            return f'https://t.me/{source_group_username}/{ChannelCommentExtractor.get_message_id(obj)}?thread={discussion_message_id}'

        # Case 3
        if not source_channel_username and not source_group_username:
            return f'https://t.me/c/{ChannelCommentExtractor.get_peer_id(obj)}/{ChannelCommentExtractor.get_message_id(obj)}?thread={discussion_message_id}'

    @staticmethod
    def extract(obj, discussion_message_id, source_message_id, source_channel_username, source_group_username, source_channel_id):
        result = ChannelCommentExtractor.extract_entities(obj)
        result['MEDIA'] = ChannelCommentExtractor.get_media(obj)

        result['FETCH_TIME']        = int(time.time())
        result['DATE']              = ChannelCommentExtractor.get_date(obj)
        result['TYPE']              = ChannelCommentExtractor.get_message_type()

        result['AUTHOR_ID']         = ChannelCommentExtractor.get_author_id(obj.from_id)
        result['AUTHOR_TYPE']       = ChannelCommentExtractor.get_author_type(obj.from_id)

        result['PEER_ID']           = ChannelCommentExtractor.get_peer_id(obj.peer_id)
        result['PEER_TYPE']         = ChannelCommentExtractor.get_peer_type(obj.peer_id)

        result['PUBLIC_URL']        = ChannelCommentExtractor.get_public_url(obj, discussion_message_id, source_message_id, source_channel_username, source_group_username)
        result['PRIVATE_URL']       = ChannelCommentExtractor.get_private_url(obj)
        result['ID']                = str(result['PRIVATE_URL'])

        result['MESSAGE_ID']        = ChannelCommentExtractor.get_message_id(obj)
        result['MESSAGE']           = ChannelCommentExtractor.get_message(obj)

        result['REPLY_PEER_TYPE']   = ChannelCommentExtractor.get_reply_peer_type(obj)
        result['REPLY_PEER_ID']     = ChannelCommentExtractor.get_reply_peer_id(obj)
        result['REPLY_LINK']        = f'https://t.me/c/{source_channel_id}/{source_message_id}'

        result['FWD_PEER_TYPE']     = ChannelCommentExtractor.get_fwd_peer_type(obj)
        result['FWD_PEER_ID']       = ChannelCommentExtractor.get_fwd_peer_id(obj)
        result['FWD_LINK']          = ChannelCommentExtractor.get_fwd_link(obj)

        result['REACTIONS']         = ChannelCommentExtractor.get_reactions(obj)
        result['REPLIES_COUNT']     = ChannelCommentExtractor.get_replies_count(obj)
        result['REACTIONS_COUNT']   = ChannelCommentExtractor.get_reactions_count(obj)
        result['VIEWS_COUNT']       = ChannelCommentExtractor.get_views_count(obj)
        result['FORWARDS_COUNT']    = ChannelCommentExtractor.get_forwards_count(obj)

        # persian_message = ChannelCommentExtractor.check_persian_character(message=obj.message)
        # if persian_message:
        #     result['TAGS'] = ChannelCommentExtractor.get_tags(message=obj.message)
        #     result['SENTIMENT'] = ChannelCommentExtractor.get_sentiment(message=obj.message)
        #     result['SENSE'] = ChannelCommentExtractor.get_sense(message=obj.message)
        # else:
        #     result['TAGS'] = None
        #     result['SENTIMENT'] = None
        #     result['SENSE'] = None
        result['TAGS'] = None
        result['SENTIMENT'] = None
        result['SENSE'] = None
        return result
