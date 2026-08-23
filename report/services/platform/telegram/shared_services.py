from typing import Optional, Dict, Any, List
from fastapi import HTTPException, UploadFile, File
import logging
import os
import tempfile

from app.startup import elastic_handler, minio_handler
from app.config import (
    TELEGRAM_INDEX_CHANNELS as INDEX_CHANNELS,
    TELEGRAM_INDEX_GROUPS as INDEX_GROUPS,
    TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES,
    TELEGRAM_INDEX_USERS as INDEX_USERS,
    TELEGRAM_INDEX_CHAT_MESSAGES as INDEX_CHAT_MESSAGES,
    MINIO_QUERIES_BUCKET_NAME as BUCKET_QUERIES,
    MINIO_TELEGRAM_CHANNEL_BUCKET_NAME as BUCKET_CHANNEL,
    MINIO_TELEGRAM_GROUP_BUCKET_NAME as BUCKET_GROUP,
    MINIO_TELEGRAM_USER_BUCKET_NAME as BUCKET_USER,
    MINIO_TELEGRAM_MEDIA_CHATS_BUCKET_NAME as BUCKET_MEDIA,
)
from utils import db_handler as db
from services.platform.telegram import channels as channels_service
from services.platform.telegram import groups as groups_service
from services.platform.telegram import users as users_service

# Logging
logger = logging.getLogger(__name__)


class TelegramService:
    """Service class for Telegram-related business logic"""
    
    @staticmethod
    def _build_search_query(search: str, index_type: str) -> Dict[str, Any]:
        """Build search query for channels, groups, or users"""
        if index_type in ["channels", "groups"]:
            search_queries = [
                {"match": {"TITLE": search}},
                {"match": {"USERNAME": search}}
            ]
            
            # Only add PEER_ID term query if search is numeric
            if search.isdigit():
                search_queries.append({"term": {"PEER_ID": int(search)}})
        elif index_type == "users":
            search_queries = [
                {"match": {"FIRST_NAME": search}},
                {"match": {"LAST_NAME": search}},
                {"match": {"USERNAME": search}},
            ]
            
            # Only add USER_ID term query if search is numeric
            if search.isdigit():
                search_queries.append({"term": {"USER_ID": int(search)}})
        else:
            raise ValueError(f"Invalid index_type: {index_type}")
        
        search_payload = {
            "size": 0,
            "query": {
                "bool": {
                    "should": search_queries,
                    "minimum_should_match": 1
                }
            },
            "aggs": {
                f"matching_{index_type}": {
                    "terms": {
                        "field": "PEER_ID" if index_type in ["channels", "groups"] else "USER_ID",
                        "size": 10000
                    }
                }
            }
        }
        
        return search_payload
    
    @staticmethod
    def _get_matching_ids(search_response: Dict[str, Any], index_type: str) -> List[int]:
        """Extract matching IDs from search response"""
        return [
            bucket["key"] 
            for bucket in search_response["aggregations"][f"matching_{index_type}"]["buckets"]
        ]
    
    @staticmethod
    def _build_messages_query(matching_ids: List[int], message_type: str, entity_type: str) -> Dict[str, Any]:
        """Build query for messages based on matching IDs and message type"""
        if matching_ids:
            if entity_type == "users":
                return {
                    "bool": {
                        "must": [
                            {"terms": {"AUTHOR_ID": matching_ids}},
                            {"match_phrase": {"TYPE": message_type}},
                            {"match_phrase": {"AUTHOR_TYPE": "USER"}}
                        ]
                    }
                }
            else:
                return {
                    "bool": {
                        "must": [
                            {"terms": {"PEER_ID": matching_ids}},
                            {"match_phrase": {"TYPE": message_type}}
                        ]
                    }
                }
        else:
            return {"match_none": {}}  # No results
    
    @staticmethod
    def _build_composite_aggregation(size: int, after: Optional[str] = None, source_name: str = "channel", source_term: str = "PEER_ID") -> Dict[str, Any]:
        """Build composite aggregation for pagination"""
        composite_agg = {
            "sources": {
                "composite": {
                    "size": size,
                    "sources": [
                        {
                            source_name: {
                                "terms": {
                                    "field": source_term
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        # Add after parameter for pagination if provided
        if after:
            composite_agg["sources"]["composite"]["after"] = {source_name: after}
        
        return composite_agg
    
    @classmethod
    async def upload_image(
        cls,
        bucket_name: str,
        entity_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """
        Generic method to upload images for channels, groups, or users
        
        Args:
            entity_id: ID of the entity (channel_id, group_id, or user_id)
            file: Uploaded image file
            
        Returns:
            Dictionary with upload result information
        """
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                # Write uploaded file to temporary file
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                
                try:
                    # Upload to MinIO with entity-specific name
                    object_name = f"{entity_id}.jpg"
                    image_url = minio_handler.create_image_url(
                        temp_file.name,
                        object_name=object_name if bucket_name != BUCKET_MEDIA else str(os.path.splitext(file.filename)[1]),
                        expiration=60,
                        bucket_name=bucket_name
                    )
                    if image_url:
                        return {
                            "success": True,
                            "url": image_url,
                            "filename": file.filename,
                            "content_type": file.content_type,
                            "size": len(content)
                        }
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to upload image to MinIO"
                        )
                        
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file.name)
                    
        except Exception as e:
            logger.error(f"Error uploading image {entity_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image: {str(e)}"
            )
    
    @classmethod
    async def get_entity_list(
        cls,
        entity_type: str,  # "channels", "groups", or "users" or "admin_peers"
        size: int = 100,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generic method to get list of channels, groups, or users
        
        Args:
            entity_type: Either "channels", "groups", or "users" or "admin_peers"
            size: Number of results to return
            after: Pagination cursor
            search: Search term for filtering
            
        Returns:
            Dictionary with entities, after_key, and has_more flag
        """
        # Validate size
        if size > 100:
            size = 100
        
        # Determine configuration based on entity type
        if entity_type == "channels":
            index_type = "channels"
            message_type = "CHANNELPOST"
            source_name = "id"
            source_term = "PEER_ID"
            search_index = INDEX_MESSAGES
        elif entity_type == "groups":
            index_type = "groups"
            message_type = "CHANNELCOMMENT"
            source_name = "id"
            source_term = "PEER_ID"
            search_index = INDEX_MESSAGES
        elif entity_type == "users":
            index_type = "users"
            message_type = "CHANNELCOMMENT"
            source_name = "id"
            source_term = "AUTHOR_ID"
            search_index = INDEX_MESSAGES
        elif entity_type == "admin_peers":
            index_type = "admin_peers"
            message_type = "CHATMESSAGE"
            source_name = "chats"
            source_term = "PEER_ID"
            search_index = INDEX_CHAT_MESSAGES
        else:
            raise ValueError(f"Invalid entity_type: {entity_type}. Must be 'channels', 'groups', 'users', or 'admin_peers'")
        
        # Build query based on search parameter
        if search:
            # Get matching entities from the appropriate index
            search_payload = cls._build_search_query(search, index_type)
            search_response = await elastic_handler.client.search(index=INDEX_CHANNELS, body=search_payload)
            matching_ids = cls._get_matching_ids(search_response, index_type)
            query = cls._build_messages_query(matching_ids, message_type, entity_type)
        else:
            if entity_type == "users":
                query = {
                    "bool": {
                        "must": [
                            {"match": {"TYPE": message_type}},
                            {"match": {"AUTHOR_TYPE": "USER"}},
                        ]
                    }
                }
            else:
                query = {"match_phrase": {"TYPE": message_type}}
        
        # Build the composite aggregation
        composite_agg = cls._build_composite_aggregation(size, after, source_name, source_term)
        payload = {
            "size": 0,
            "track_total_hits": True,
            "query": query,
            "aggs": composite_agg,
        }
        
        response = await elastic_handler.client.search(index=search_index, body=payload)
        buckets = response['aggregations']['sources']['buckets']
        
        # Get the after_key for next page
        after_key = response['aggregations']['sources'].get('after_key')
        
        return {
            "entities": buckets,  # Keep consistent response format
            "after_key": after_key,
            "has_more": after_key is not None
        }
    
    @classmethod
    async def get_channels_list(
        cls,
        size: int = 100,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of Telegram channels"""
        channels_list = await cls.get_entity_list("channels", size, after, search)
        for channel in channels_list['entities']:
            channel['key']['DATA']  = await channels_service.get_channel_details_overview(channel['key']['id'])
        return channels_list
    
    @classmethod
    async def get_admin_peers_list(
        cls,
        size: int = 100,
        after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get list of Telegram admin peers"""
        return await cls.get_entity_list("admin_peers", size, after, search=None)
    
    @classmethod
    async def get_groups_list(
        cls,
        size: int = 100,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of Telegram groups"""
        groups_list = await cls.get_entity_list("groups", size, after, search)
        for group in groups_list['entities']:
            group['key']['DATA']  = await groups_service.get_group_details_overview(group['key']['id'])
        return groups_list
    
    @classmethod
    async def get_users_list(
        cls,
        size: int = 100,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of Telegram users"""
        users_list = await cls.get_entity_list("users", size, after, search)
        for user in users_list['entities']:
            user['key']['DATA']  = await users_service.get_user_details_overview(user['key']['id'])
        return users_list
    
    @classmethod
    async def upload_channel_image(
        cls,
        channel_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """Upload image for a Telegram channel"""
        return await cls.upload_image(bucket_name=BUCKET_CHANNEL, entity_id=channel_id, file=file)
    
    @classmethod
    async def upload_group_image(
        cls,
        group_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """Upload image for a Telegram group"""
        return await cls.upload_image(bucket_name=BUCKET_GROUP, entity_id=group_id, file=file)
    
    @classmethod
    async def upload_user_image(
        cls,
        user_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """Upload image for a Telegram user"""
        return await cls.upload_image(bucket_name=BUCKET_USER, entity_id=user_id, file=file) 

    @classmethod
    async def upload_media_file(
        cls,
        media_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """Upload media file for a Telegram user"""
        return await cls.upload_image(bucket_name=BUCKET_MEDIA, entity_id=media_id, file=file) 

    @classmethod
    async def upload_query_image(
        cls,
        query_id: int,
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        """Upload image for a Telegram user"""
        return await cls.upload_image(entity_type="queries", bucket_name=BUCKET_QUERIES, entity_id=query_id, file=file)

    @classmethod
    async def create_channel(
        cls,
        data: dict,
    ) -> Dict[str, Any]:
        """Create a new Telegram channel"""
        return db.create_telegram_peer(data)

    @classmethod
    async def update_channel(
        cls,
        channel_id: int,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a Telegram channel"""
        channel = db.get_telegram_peer(id=channel_id)
        if not channel['subscriber']:
            return db.update_telegram_peer(data, id=channel_id)
        else:
            raise HTTPException(status_code=400, detail="An account is already associated with this channel, Can't update")

    @classmethod
    async def block_channel(
        cls,
        channel_id: int,
    ) -> Dict[str, Any]:
        """Block a Telegram channel"""
        return db.block_telegram_peer(id=channel_id)

    @classmethod
    async def unblock_channel(
        cls,
        channel_id: int,
    ) -> Dict[str, Any]:
        """Unblock a Telegram channel"""
        return db.unblock_telegram_peer(id=channel_id)
