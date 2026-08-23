import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

import models
import schemas


class TestTelegramChannelsAPI:
    """Test suite for Telegram Channels API endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_telegram_channels_empty(self, async_client: AsyncClient):
        """Test getting all telegram channels when database is empty."""
        response = await async_client.get("/telegram/channels")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_telegram_channel_by_id(self, async_client: AsyncClient, sample_telegram_channel):
        """Test getting a telegram channel by ID."""
        response = await async_client.get(f"/telegram/channels?id={sample_telegram_channel.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_telegram_channel.id
        assert data["key"] == sample_telegram_channel.key

    @pytest.mark.asyncio
    async def test_get_telegram_channel_by_key(self, async_client: AsyncClient, sample_telegram_channel):
        """Test getting a telegram channel by key."""
        response = await async_client.get(f"/telegram/channels?key={sample_telegram_channel.key}")
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == sample_telegram_channel.key

    @pytest.mark.asyncio
    async def test_get_telegram_channel_by_value(self, async_client: AsyncClient, sample_telegram_channel):
        """Test getting a telegram channel by value."""
        response = await async_client.get(f"/telegram/channels?value={sample_telegram_channel.value}")
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == sample_telegram_channel.value

    @pytest.mark.asyncio
    async def test_get_telegram_channel_by_tag(self, async_client: AsyncClient, sample_telegram_channel):
        """Test getting a telegram channel by tag."""
        response = await async_client.get(f"/telegram/channels?tag={sample_telegram_channel.tag}")
        assert response.status_code == 200
        data = response.json()
        assert data["tag"] == sample_telegram_channel.tag

    @pytest.mark.asyncio
    async def test_get_telegram_channel_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent telegram channel."""
        response = await async_client.get("/telegram/channels?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Channel does not exist"

    @pytest.mark.asyncio
    async def test_create_telegram_channel(self, async_client: AsyncClient):
        """Test creating a new telegram channel."""
        channel_data = {
            "key": "new_test_channel",
            "value": "new_test_value",
            "tag": "new_test_tag",
            "chat_id": 987654321,
            "access_hash": 123456789,
            "in_progress": False,
            "blocked": False,
            "subscribed_by": 1
        }
        
        response = await async_client.post("/telegram/channels", json=channel_data)
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == channel_data["key"]
        assert data["value"] == channel_data["value"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_telegram_channel_duplicate_key(self, async_client: AsyncClient, sample_telegram_channel):
        """Test creating a telegram channel with duplicate key."""
        channel_data = {
            "key": sample_telegram_channel.key,  # Duplicate key
            "value": "different_value",
            "tag": "different_tag",
            "chat_id": 111222333,
            "access_hash": 444555666,
            "in_progress": False,
            "blocked": False,
            "subscribed_by": 1
        }
        
        response = await async_client.post("/telegram/channels", json=channel_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_telegram_channel(self, async_client: AsyncClient, sample_telegram_channel):
        """Test updating a telegram channel."""
        update_data = {
            "value": "updated_value",
            "tag": "updated_tag",
            "blocked": True,
            "in_progress": True
        }
        
        response = await async_client.put(f"/telegram/channels?id={sample_telegram_channel.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == update_data["value"]
        assert data["tag"] == update_data["tag"]
        assert data["blocked"] == update_data["blocked"]
        assert data["in_progress"] == update_data["in_progress"]

    @pytest.mark.asyncio
    async def test_update_telegram_channel_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent telegram channel."""
        update_data = {"value": "updated_value"}
        response = await async_client.put("/telegram/channels?id=99999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Channel does not exist"

    @pytest.mark.asyncio
    async def test_delete_telegram_channel(self, async_client: AsyncClient, sample_telegram_channel):
        """Test deleting a telegram channel."""
        response = await async_client.delete(f"/telegram/channels?id={sample_telegram_channel.id}")
        assert response.status_code == 200
        assert response.json() == "successfully deleted the channel"

        # Verify it's actually deleted
        get_response = await async_client.get(f"/telegram/channels?id={sample_telegram_channel.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_telegram_channel_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent telegram channel."""
        response = await async_client.delete("/telegram/channels?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Channel does not exist"

    @pytest.mark.asyncio
    async def test_get_telegram_channels_with_multiple_channels(self, async_client: AsyncClient, db_session: Session):
        """Test getting all telegram channels when multiple exist."""
        # Create multiple channels
        channels_data = [
            {"key": "channel1", "value": "value1", "tag": "tag1", "chat_id": 111, "access_hash": 111, "subscribed_by": 1},
            {"key": "channel2", "value": "value2", "tag": "tag2", "chat_id": 222, "access_hash": 222, "subscribed_by": 1},
            {"key": "channel3", "value": "value3", "tag": "tag3", "chat_id": 333, "access_hash": 333, "subscribed_by": 1},
        ]
        
        for channel_data in channels_data:
            channel = models.TelegramChannel(**channel_data)
            db_session.add(channel)
        db_session.commit()
        
        response = await async_client.get("/telegram/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the 3 we just created
        assert any(channel["key"] == "channel1" for channel in data)
        assert any(channel["key"] == "channel2" for channel in data)
        assert any(channel["key"] == "channel3" for channel in data)

    @pytest.mark.asyncio
    async def test_get_telegram_channels_by_subscriber(self, async_client: AsyncClient, db_session: Session):
        """Test getting telegram channels by subscriber."""
        # Create channels with different subscribers
        channels_data = [
            {"key": "sub1_channel", "value": "value1", "tag": "tag1", "chat_id": 111, "access_hash": 111, "subscribed_by": 1},
            {"key": "sub2_channel", "value": "value2", "tag": "tag2", "chat_id": 222, "access_hash": 222, "subscribed_by": 2},
            {"key": "sub1_channel2", "value": "value3", "tag": "tag3", "chat_id": 333, "access_hash": 333, "subscribed_by": 1},
        ]
        
        for channel_data in channels_data:
            channel = models.TelegramChannel(**channel_data)
            db_session.add(channel)
        db_session.commit()
        
        response = await async_client.get("/telegram/channels?subscribed_by=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # At least 2 channels for subscriber 1
        assert all(channel["subscribed_by"] == 1 for channel in data) 