# import logging
# import re
# import json
# from datetime import datetime, date, timedelta
# from fastapi import HTTPException

# from app.startup import elastic_handler
# from queries.queries import QueryTypes
# from services import services
# logger = logging.getLogger(__name__)

# async def get_sourcetracing(search_text: str, start_date: str, end_date: str, size: int = 10) -> list[dict]:
#     template = services.jinja_template_generator(path=QueryTypes.InstagramSourcetracing)
#     payload = template.render(search_text=search_text, start_date=start_date, end_date=end_date, size=size)
#     response = await elastic_handler.client.search(index="instagram_post_v4", body=payload)
#     hits = response["hits"]["hits"]
#     return [
#         {
#             "username": h["_source"].get("username", "N/A"),
#             "caption": h["_source"].get("caption", ""),
#             "like_count": h["_source"].get("like_count", 0),
#             "POST_URL": h["_source"].get("url", "N/A"),
#             "taken_at": h["_source"].get("taken_at")
#         }
#         for h in hits
#     ]
