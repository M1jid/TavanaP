import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

import models
import schemas


class TestTelegramPeersAPI:
    """Test suite for Telegram Peers API endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_telegram_peers_empty(self, async_client: AsyncClient):
        """Test getting all telegram peers when database is empty."""
        response = await async_client.get("/telegram/peers")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_telegram_peer_by_id(self, async_client: AsyncClient, sample_telegram_peer):
        """Test getting a telegram peer by ID."""
        response = await async_client.get(f"/telegram/peers?id={sample_telegram_peer.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_telegram_peer.id
        assert data["username"] == sample_telegram_peer.username

    @pytest.mark.asyncio
    async def test_get_telegram_peer_by_peer_id(self, async_client: AsyncClient, sample_telegram_peer):
        """Test getting a telegram peer by peer_id."""
        response = await async_client.get(f"/telegram/peers?peer_id={sample_telegram_peer.peer_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["peer_id"] == sample_telegram_peer.peer_id

    @pytest.mark.asyncio
    async def test_get_telegram_peer_by_username(self, async_client: AsyncClient, sample_telegram_peer):
        """Test getting a telegram peer by username."""
        response = await async_client.get(f"/telegram/peers?username={sample_telegram_peer.username}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_telegram_peer.username

    @pytest.mark.asyncio
    async def test_get_telegram_peer_by_url(self, async_client: AsyncClient, sample_telegram_peer):
        """Test getting a telegram peer by URL."""
        response = await async_client.get(f"/telegram/peers?url={sample_telegram_peer.url}")
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == sample_telegram_peer.url

    @pytest.mark.asyncio
    async def test_get_telegram_peer_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent telegram peer."""
        response = await async_client.get("/telegram/peers?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Peer does not exist"

    @pytest.mark.asyncio
    async def test_create_telegram_peer(self, async_client: AsyncClient):
        """Test creating a new telegram peer."""
        peer_data = {
            "username": "new_test_peer",
            "url": "https://t.me/new_test_peer",
            "peer_id": 999888777,
            "blocked": False,
            "linked_peer_id": None,
            "subscriber": 1,
            "is_channel": True,
            "on_waiting": False
        }
        
        response = await async_client.post("/telegram/peers", json=peer_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == peer_data["username"]
        assert data["peer_id"] == peer_data["peer_id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_telegram_peer_duplicate_peer_id(self, async_client: AsyncClient, sample_telegram_peer):
        """Test creating a telegram peer with duplicate peer_id."""
        peer_data = {
            "username": "duplicate_peer",
            "url": "https://t.me/duplicate_peer",
            "peer_id": sample_telegram_peer.peer_id,  # Duplicate peer_id
            "blocked": False,
            "linked_peer_id": None,
            "subscriber": 1,
            "is_channel": True,
            "on_waiting": False
        }
        
        response = await async_client.post("/telegram/peers", json=peer_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_telegram_peer(self, async_client: AsyncClient, sample_telegram_peer):
        """Test updating a telegram peer."""
        update_data = {
            "username": "updated_username",
            "blocked": True,
            "notes": "Updated for testing"
        }
        
        response = await async_client.put(f"/telegram/peers?id={sample_telegram_peer.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == update_data["username"]
        assert data["blocked"] == update_data["blocked"]

    @pytest.mark.asyncio
    async def test_update_telegram_peer_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent telegram peer."""
        update_data = {"username": "updated_username"}
        response = await async_client.put("/telegram/peers?id=99999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Peer does not exist"

    @pytest.mark.asyncio
    async def test_delete_telegram_peer(self, async_client: AsyncClient, sample_telegram_peer):
        """Test deleting a telegram peer."""
        response = await async_client.delete(f"/telegram/peers?id={sample_telegram_peer.id}")
        assert response.status_code == 200
        assert response.json() == "successfully deleted the peer"

        # Verify it's actually deleted
        get_response = await async_client.get(f"/telegram/peers?id={sample_telegram_peer.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_telegram_peer_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent telegram peer."""
        response = await async_client.delete("/telegram/peers?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Peer does not exist"

    @pytest.mark.asyncio
    async def test_get_telegram_peers_with_multiple_peers(self, async_client: AsyncClient, db_session: Session):
        """Test getting all telegram peers when multiple exist."""
        # Create multiple peers
        peers_data = [
            {"username": "peer1", "url": "https://t.me/peer1", "peer_id": 111, "subscriber": 1, "is_channel": True},
            {"username": "peer2", "url": "https://t.me/peer2", "peer_id": 222, "subscriber": 1, "is_channel": True},
            {"username": "peer3", "url": "https://t.me/peer3", "peer_id": 333, "subscriber": 1, "is_channel": True},
        ]
        
        for peer_data in peers_data:
            peer = models.TelegramPeer(**peer_data)
            db_session.add(peer)
        db_session.commit()
        
        response = await async_client.get("/telegram/peers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the 3 we just created
        assert any(peer["username"] == "peer1" for peer in data)
        assert any(peer["username"] == "peer2" for peer in data)
        assert any(peer["username"] == "peer3" for peer in data) 