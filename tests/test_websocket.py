from unittest.mock import AsyncMock
import pytest

@pytest.mark.asyncio
async def test_websocket_connection():
    mock_ws = AsyncMock()
    mock_ws.connect.return_value = AsyncMock()
    
    with patch('websockets.connect', mock_ws):
        pool = WebSocketPool("wss://test.com", pool_size=2)
        conn = await pool.get_connection()
        assert conn is not None 