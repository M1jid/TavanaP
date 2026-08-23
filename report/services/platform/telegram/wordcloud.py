from fastapi import HTTPException, status

from collections import Counter
from typing import List
import emoji
import re
import json

from hazm import Normalizer, word_tokenize, stopwords_list

from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from app.startup import elastic_handler
from services import services
from queries.queries import QueryTypes
from logging import getLogger

from utils.routing_roles import config as routing_roles

logger = getLogger(__name__)


def is_emoji(word):
    """Check if a word contains emoji characters"""
    return any(char in emoji.EMOJI_DATA for char in word)


def is_short_english_word(word):
    """Check if a word is a short English word (1-4 characters)"""
    return re.fullmatch(r"[a-zA-Z]{1,4}", word) is not None


async def _process_wordcloud_data(payload: str):
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    hits = response.get("hits", {}).get("hits", [])
    
    # Process text for wordcloud
    normalizer = Normalizer()
    stopwords = set(stopwords_list())
    
    all_words = []
    for hit in hits:
        message = hit["_source"].get("MESSAGE", "") or hit["_source"].get("CLEANED_MESSAGE", "")
        if message:
            # Normalize and tokenize
            normalized = normalizer.normalize(message)
            tokens = word_tokenize(normalized)
            
            # Filter tokens
            filtered_tokens = []
            for token in tokens:
                # Skip if token is too short, is emoji, is short English word, or is stopword
                if (len(token) < 2 or 
                    is_emoji(token) or 
                    is_short_english_word(token) or 
                    token in stopwords or
                    token.isdigit()):
                    continue
                filtered_tokens.append(token)
            
            all_words.extend(filtered_tokens)
    
    # Count word frequencies
    word_counts = Counter(all_words)
    
    # Convert to list of dictionaries for response
    wordcloud_data = [
        {"text": word, "value": count}
        for word, count in word_counts.most_common(50)  # Top 100 words
    ]
    
    return {
        "wordcloud": wordcloud_data,
        "total_words": len(all_words),
        "unique_words": len(word_counts)
    }

async def get_wordcloud(
    search_text: str,
    start_date: str,
    end_date: str,
    selected_channels: List[int],
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramWordCloud)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        search_text=search_text,
        selected_channels=selected_channels,
    )

    return await _process_wordcloud_data(payload)


async def get_owned_channels_wordcloud(
    channel_id: int,
    start_date: str,
    end_date: str,
):
    """Get Telegram owned channels report"""
    channel = [channel for channel in routing_roles if abs(channel['channel_id']) == channel_id]
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    channel = channel[0]
    roles = channel['roles']
    channel_id = str(channel['channel_id'])[1:]
    channel_name = channel['name']
    conditions = []

    for role in roles:
        must = [{"match_phrase": {"MESSAGE": term}} for term in role["must"]]
        should = [{"match_phrase": {"MESSAGE": term}} for term in role["should"]]
        must_not = [{"match_phrase": {"MESSAGE": term}} for term in role["must_not"]]
        
        # Only add condition if there's at least one clause
        if must or should or must_not:
            condition = {"bool": {}}
            
            if must:
                condition["bool"]["must"] = must
            if should:
                condition["bool"]["should"] = should
                condition["bool"]["minimum_should_match"] = 1
            if must_not:
                condition["bool"]["must_not"] = must_not
                
            conditions.append(condition)

    template = services.jinja_template_generator(path=QueryTypes.TelegramOwnedChannelsWordCloud)
    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        conditions=conditions,
    )
    payload = json.loads(payload)
    payload['query']['bool']['must'][1]['bool']['should'] = payload['query']['bool']['must'][1]['bool']['should'][0]

    return await _process_wordcloud_data(payload)


async def get_user_wordcloud(
    user_id: int,
    start_date: str,
    end_date: str,
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramUserWordCloud)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )

    return await _process_wordcloud_data(payload)


async def get_channel_wordcloud(
    channel_id: int,
    start_date: str,
    end_date: str,
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramChannelWordCloud)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        channel_id=channel_id,
    )

    return await _process_wordcloud_data(payload)


async def get_group_wordcloud(
    group_id: int,
    start_date: str,
    end_date: str,
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramGroupWordCloud)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        group_id=group_id,
    )

    return await _process_wordcloud_data(payload)
