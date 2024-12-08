import asyncio

import websockets


def create_websocket():
    """
    Establishes a connection to the GUI via WebSocket.
    """
    try:
        websocket_url = "http://localhost:3000/ws/real-time"
        websocket = asyncio.run(websockets.connect(websocket_url))
        print("Connected to GUI WebSocket at:", websocket_url)
        return websocket
    except Exception as e:
        print(f"Error connecting to GUI WebSocket: {e}")
        return None
