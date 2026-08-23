import re

from utils.models_handler import get_disticnt_tag_army
import utils.routing_roles as routing_roles

import logging
logger = logging.getLogger(__name__)

class ChannelsRouter:
    """
    ChannelsRouter with safe, debounced, content-hash-based hot-reload of routing_roles.py.
    Prevents infinite reload loops and log spam from duplicate FS events.
    """
    CHARS_TO_REMOVE = (
        ',', '.', '/', '<', '>', '?', "'", '"', ';', ':', ']', '[', '{', '}', '\\', '/', '+', '=', '_',
        '-', ')', '(', '*', '&', '^', '%', '$', '#', '@', '!', '~', '`', 'ٰ', '‌', 'ٔ', 'ٔ', 'ء', '؟',
        '؛', '«', '»', 'ّ', 'َ', 'ِ', 'ُ', 'ً', 'ٍ', 'ٌ', 'ْ', '`', '!', '٬', '٫', 'ریال', '٪', '×',
        '،', '،', 'ـ', '_', '|'
    )

    def __init__(self):
        """
        """
        self.channel_configs = routing_roles.config

    def _normalize_message(self, message: str) -> str:
        # Replace ZWNJ with a normal space and strip your punctuation list
        msg = message.replace('\u200c', ' ')
        for ch in self.CHARS_TO_REMOVE:
            msg = msg.replace(ch, '')
        # Normalize multiple spaces to single
        msg = re.sub(r'\s+', ' ', msg).strip()
        return msg

    def match_channels(self, message: str):
        """
        Returns:
          List[{"channel_id": int, "matched_roles": List[role]}]
        """
        normalized = self._normalize_message(message)
        results = []

        configs = list(self.channel_configs)

        for channel in configs:
            roles = channel.get('roles', [])
            target_channel_id = channel.get('channel_id')
            matched_roles = []

            for role in roles:
                must = role.get('must') or []
                should = role.get('should') or []
                must_not = role.get('must_not') or []

                def _has_any(words):
                    return any(re.search(rf'(^|\s){re.escape(w)}($|\s)', normalized) for w in words)

                def _has_all(words):
                    return all(re.search(rf'(^|\s){re.escape(w)}($|\s)', normalized) for w in words)

                must_pass = _has_all(must) if must else True
                should_pass = _has_any(should) if should else True
                must_not_fail = not _has_any(must_not) if must_not else True

                if must_pass and should_pass and must_not_fail:
                    matched_roles.append(role)

            if matched_roles:
                results.append({
                    'channel_id': target_channel_id,
                    'matched_roles': matched_roles
                })

        return results
