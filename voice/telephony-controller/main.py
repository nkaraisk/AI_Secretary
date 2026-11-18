import asyncio
import base64
import getpass
import json

from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake

# Identifies the account that authenticates with Asterisk. Credentials establish permission.
ARI_USERNAME = "ai-secretary-dev"

# Names the application that will handle calls. The application name identifies where call events should go.
ARI_APPLICATION = "ai-secretary"

# This connection delivers JSON events.
ARI_EVENTS_URL = (
    f"ws://127.0.0.1:18088/ari/events?app={ARI_APPLICATION}"
)

# The WebSocket URL receives events. This HTTP URL sends commands.
ARI_HTTP_URL = "http://127.0.0.1:18088/ari"


# A helper function that keeps authentication and HTTP mechanics out of our event-handling code.
def send_ari_command(
    path: str,
    headers: dict[str, str],
    parameters: dict[str, str] | None = None,
) -> None:
    url = f"{ARI_HTTP_URL}{path}"

    if parameters:
        url = f"{url}?{urlencode(parameters)}" # urlencode safely formats query parameters.

    request = Request(
        url,
        headers=headers,
        method="POST",
    )

    # Connect directly to the local SSH tunnel, ignoring system proxies.
    opener = build_opener(ProxyHandler({}))

    with opener.open(request, timeout=5) as response:
        response.read()

# Answer-and-greet function
async def answer_and_greet(
    channel_id: str,
    headers: dict[str, str],
) -> None:
    channel_path = f"/channels/{quote(channel_id, safe='')}" # safely puts the channel ID into a URL path

    try:
        await asyncio.to_thread( # await: ensures answering completes before we request playback.
            send_ari_command,    # asyncio.to_thread: runs the blocking HTTP operation in a worker thread so it doesn’t block the entire asynchronous event loop.
            f"{channel_path}/answer",
            headers,
        )
        print("Test call answered.")

        await asyncio.to_thread( # ensures answering completes before we request playback.
            send_ari_command,    # asyncio.to_thread: runs the blocking HTTP operation in a worker thread so it doesn’t block the entire asynchronous event loop.
            f"{channel_path}/play",
            headers,
            {"media": "sound:hello-world"}, # Refers to an audio prompt on the PBX
        )
        print("Greeting playback requested.")

    except HTTPError as error:
        if error.code == 404:
            print("ARI resource not found; the caller may have hung up.")
        else:
            print(f"ARI command failed: HTTP {error.code}.")

    except (URLError, TimeoutError, OSError):
        print("Could not complete the call command. Check the SSH tunnel.")


# Defines a function that can wait for network activity while allowing other asynchronous tasks to run.
async def listen_for_events(password: str) -> None:
    credentials = f"{ARI_USERNAME}:{password}"
    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("ascii")

    # Authorization header supplies the ARI credentials without including them in the URL.
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    # Opens the connection and closes it when we leave that block
    async with connect(
        ARI_EVENTS_URL,
        subprotocols=["ari"],
        additional_headers=headers,
        proxy=None, # Ensures this local connection goes directly to our SSH tunnel.
        open_timeout=10,
        close_timeout=5,
        ping_interval=20,
        ping_timeout=20,
        max_size=1_048_576,
    ) as websocket:
        print(f"Connected to Asterisk. Application: {ARI_APPLICATION}")
        print("Waiting for events. Press Ctrl+C to stop.")

        # Waits for incoming messages without repeatedly polling Asterisk.
        async for message in websocket:
            # Converts a JSON message into a Python object we can inspect.
            event = json.loads(message)

            # Events can contain personal data. Print only their type.
            event_type = event.get("type", "Unknown")
            print(f"Event: {event_type}")

            # StasisStart means a channel has entered our application. Ordinary calls between 1001 and 1002 won’t automatically enter it.
            if event_type == "StasisStart":
                channel_id = event["channel"]["id"]
                await answer_and_greet(channel_id, headers)

            if event_type == "ApplicationReplaced":
                print("Another connection replaced this application.")
                return

        print("Asterisk closed the event connection.")


def main() -> None:
    try:
        # Reads our password without displaying it or storing it in source code.
        password = getpass.getpass("ARI password: ")

        if not password:
            print("A password is required.")
            return

        # Starts the event loop that executes our asynchronous function.
        asyncio.run(listen_for_events(password))

    except InvalidHandshake:
        print(
            "WebSocket connection rejected. Check your ARI credentials "
            "and that the tunnel points to Asterisk."
        )

    except (OSError, TimeoutError):
        print(
            "Could not maintain the connection. "
            "Check the VM and SSH tunnel, then run again."
        )

    except ConnectionClosed:
        print("The connection was interrupted. Check the tunnel and run again.")

    except (json.JSONDecodeError, AttributeError):
        print("Received an unexpected event format. Stopping.")

    except KeyboardInterrupt:
        print("\nController stopped.")


if __name__ == "__main__":
    main()