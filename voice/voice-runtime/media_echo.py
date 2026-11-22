import asyncio
import json

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed


async def echo_call(connection: ServerConnection) -> None:
    echoed = 0

    try:
        async for message in connection: # Waits for the next complete WebSocket message.
            # Asterisk sends two kinds on the media connection.
            # Audio arrives as a binary message, which Python receives as bytes.
            # Control information arrives as text, which Python receives as str.
            if isinstance(message, bytes):
                await connection.send(message) # This is the actual echo.
                echoed += 1
                continue # Moves to the next incoming message so those audio bytes never reach the JSON parser.

            event = json.loads(message) # Handles the text side.
            if event.get("event") == "MEDIA_START":
                print(f"Media started. Codec: {event.get('format')}")

    except ConnectionClosed:
        print("Media connection closed during transfer.")
    finally:
        print(f"Session ended. Binary messages echoed: {echoed}")


async def main() -> None:
    # serve() gives each connection its own handler.
    # This way the server calls a function when a client connects. The server supplies that client’s connection argument.
    server = await serve(
        echo_call,
        "127.0.0.1",
        18765,
        subprotocols=["media"],
        compression=None,
    )
    print("Media echo listening on 127.0.0.1:18765")
    await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Media echo stopped.")