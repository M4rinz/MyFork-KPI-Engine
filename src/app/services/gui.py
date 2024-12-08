import asyncio

import websockets


def create_websocket():
    """
    Establishes a connection to the GUI via WebSocket.

    This function attempts to establish a WebSocket connection with the GUI
    at the specified URL. It uses the `websockets` library and `asyncio` to
    connect asynchronously. If the connection is successful, it returns the 
    WebSocket object. Otherwise, it catches and prints any exceptions and 
    returns `None`.

    :return: The WebSocket connection object if successful, otherwise `None`.
    :rtype: websockets.client.WebSocketClientProtocol or None
    """
    try:
        websocket_url = "http://localhost:3000/ws/real-time"
        websocket = asyncio.run(websockets.connect(websocket_url))
        print("Connected to GUI WebSocket at:", websocket_url)
        return websocket
    except Exception as e:
        print(f"Error connecting to GUI WebSocket: {e}")
        return None
