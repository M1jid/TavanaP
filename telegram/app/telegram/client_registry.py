"""
Client Registry for managing Telegram AccountManager instances globally.
This provides a clean way to access clients from anywhere in the application.
"""
import asyncio
from typing import List, Optional
from app.telegram.account_manager import AccountManager

# Global registry
_clients: List[AccountManager] = []
_clients_lock = asyncio.Lock()


class ClientRegistry:
    """Registry for managing Telegram clients globally"""
    
    @staticmethod
    async def add_client(client: AccountManager):
        """Add a client to the registry"""
        async with _clients_lock:
            _clients.append(client)
    
    @staticmethod
    async def remove_client(client: AccountManager):
        """Remove a client from the registry"""
        async with _clients_lock:
            if client in _clients:
                _clients.remove(client)
    
    @staticmethod
    async def get_all_clients() -> List[AccountManager]:
        """Get a snapshot of all clients"""
        async with _clients_lock:
            return _clients.copy()
    
    @staticmethod
    async def get_client_by_phone(phone: int) -> Optional[AccountManager]:
        """Find a client by phone number"""
        async with _clients_lock:
            for client in _clients:
                if client.account_phone == phone:
                    return client
        return None
    
    @staticmethod
    async def get_client_by_id(id: int) -> Optional[AccountManager]:
        """Find a client by id"""
        async with _clients_lock:
            for client in _clients:
                if client.telegram_client.client_entity.id == id:
                    return client
        return None

    @staticmethod
    async def get_admin_clients() -> List[AccountManager]:
        """Get all clients with admin_listener role"""
        async with _clients_lock:
            return [client for client in _clients if 'admin_listener' in client.roles]
    
    @staticmethod
    async def clear_all():
        """Clear all clients from registry"""
        async with _clients_lock:
            _clients.clear()


# Convenience functions for backward compatibility
async def add_client(client: AccountManager):
    """Add a client to the registry"""
    await ClientRegistry.add_client(client)


async def get_client_by_phone(phone: int) -> Optional[AccountManager]:
    """Find a client by phone number"""
    return await ClientRegistry.get_client_by_phone(phone)


async def get_client_by_id(id: int) -> Optional[AccountManager]:
    """Find a client by id"""
    return await ClientRegistry.get_client_by_id(id)


async def get_all_clients() -> List[AccountManager]:
    """Get a snapshot of all clients"""
    return await ClientRegistry.get_all_clients()


async def get_admin_clients() -> List[AccountManager]:
    """Get all clients with admin_listener role"""
    return await ClientRegistry.get_admin_clients()
