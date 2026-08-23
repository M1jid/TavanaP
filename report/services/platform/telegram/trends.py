import json
from datetime import datetime

from services import services
from queries.queries import QueryTypes
from app.startup import elastic_handler
from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from services.platform.telegram import channels as channels_service
from services.platform.telegram import groups as groups_service


async def _process_trends_data(payload: str, sort: str):
    """
    Shared function to process trends data from Elasticsearch response.
    This function contains the common logic used by both get_trends_title and get_trends_overview.
    """

    payload = json.loads(payload)
    if sort == "DATE":
        payload['sort'] = [{"DATE": {"order": "desc"}}]
    if sort == "FORWARDS":
        payload['sort'] = [{"FORWARDS_COUNT": {"order": "desc"}}]
    if sort == "VIEWS":
        payload['sort'] = [{"VIEWS_COUNT": {"order": "desc"}}]
    if sort == "REACTIONS":
        payload['sort'] = [{"REACTIONS_COUNT": {"order": "desc"}}]
    if sort == "COMMENTS":
        payload['sort'] = [{"REPLIES_COUNT": {"order": "desc"}}]

    # logger.info(json.dumps(payload, indent=4, ensure_ascii=False))
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    trends = response['aggregations']['trends']['buckets']
    all_peer_ids = set()

    for trend in trends:
        for post in trend['top_messages']['hits']['hits']:
            src = post['_source']
            peer_id = src.get('PEER_ID')
            if peer_id:
                all_peer_ids.add(str(peer_id))
    
    channel_info = await channels_service.get_channels_overview(list(all_peer_ids))

    result = []
    for trend in trends:
        top_posts = []
        for post in trend['top_messages']['hits']['hits']:
            src = post['_source']
            date_val = src.get('DATE')
            hour_val, day_val = None, None

            dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
            hour_val = dt.strftime("%H:%M")
            day_val = dt.strftime("%Y-%m-%d")

            peer_id = src.get("PEER_ID")
            channel_data = channel_info.get(peer_id, {"USERNAME": "", "IMG": ""})

            url = ""
            if src['TYPE'] == 'CHANNELPOST':
                url = channels_service.get_channel_image_url(channel_id=int(peer_id))
            elif src['TYPE'] == 'CHANNELCOMMENT':
                url = await groups_service.get_group_image_url(group_id=int(peer_id))

            top_posts.append({
                **src,
                'hour': hour_val,
                'day': day_val,
                'USERNAME': channel_data['USERNAME'],
                'IMG': url,
                'replayes_count':src.get('REPLIES_COUNT'),
                'REACTIONS_COUNT':src.get('REACTIONS_COUNT'),
                "HASHTAGS":src.get('HASHTAGS'),
                "REACTIONS":src.get('REACTIONS'),
                "PEER_ID": peer_id,
            })

        result.append({
            'id': trend['key'],
            'platform': 'telegram',
            'name': trend['key'],
            'doc_count': trend['doc_count'],
            'sentiment': max(trend["sentiment"]["buckets"], key=lambda x: x["doc_count"])["key"] if trend["sentiment"]["buckets"] else "unknown",
            'icon': 'None',
            'history': [time_range['doc_count'] for time_range in trend['history']['buckets']],
            'sentimentBreakdown': {sense["key"]: sense["doc_count"] for sense in trend["sentiment"]["buckets"]},
            'senseBreakdown': {sense["key"]: sense["doc_count"] for sense in trend["sense"]["buckets"]},
            'stats': {
                'reactions': trend['reactions']['value'],
                'comments': trend['comments']['value'],
                'forwards': trend['forwards']['value'],
                'views': trend['views']['value'],
            },
            'top_posts': top_posts
        })

    return result

async def get_trends_title(title: str, start_date: str, end_date: str, sort: str):
    template = services.jinja_template_generator(path=QueryTypes.TelegramTopTrendsTitle)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        title=title,
    )

    return await _process_trends_data(payload, sort)

async def get_trends_overview(start_date: str, end_date: str, sort: str):
    template = services.jinja_template_generator(path=QueryTypes.TelegramTopTrendsOverview)

    payload = template.render(
        start_date=start_date,
        end_date=end_date,
    )

    return await _process_trends_data(payload, sort)
