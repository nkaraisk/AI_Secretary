import asyncio
import base64
import getpass
import json

from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake
from uuid import uuid4  # Creates a unique ID for each greeting playback.

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
    *, # Arguments after this must be supplied by name.
    method: str = "POST", # The default remains POST, so the existing calls still work.
) -> None:
    url = f"{ARI_HTTP_URL}{path}"

    if parameters:
        url = f"{url}?{urlencode(parameters)}" # urlencode safely formats query parameters.

    request = Request(
        url,
        headers=headers,
        method=method,
    )

    # Connect directly to the local SSH tunnel, ignoring system proxies.
    opener = build_opener(ProxyHandler({}))

    with opener.open(request, timeout=5) as response:
        response.read()


# Function for hanging up
async def hang_up(
    channel_id: str,
    headers: dict[str, str],
) -> None:
    channel_path = f"/channels/{quote(channel_id, safe='')}"

    try:
        await asyncio.to_thread(
            send_ari_command,
            channel_path,
            headers,
            method="DELETE",
        )
        print("Hangup request accepted.")

    except HTTPError as error:
        if error.code == 404: # The caller might hang up just before our request reaches Asterisk. In that case, the channel is already gone.
            print("Channel already gone; no further hangup needed.")
        else:
            print(f"Hangup request failed: HTTP {error.code}.")

    except (URLError, TimeoutError, OSError):
        print("Could not send the hangup request. Check the SSH tunnel.")



# Answer-and-greet function
async def answer_and_greet(
    channel_id: str,
    headers: dict[str, str],
    playback_channels: dict[str, str],
) -> None:
    channel_path = f"/channels/{quote(channel_id, safe='')}" # safely puts the channel ID into a URL path
    playback_id = str(uuid4())

    try:
        await asyncio.to_thread( # await: ensures answering completes before we request playback.
            send_ari_command,    # asyncio.to_thread: runs the blocking HTTP operation in a worker thread so it doesn’t block the entire asynchronous event loop.
            f"{channel_path}/answer",
            headers,
        )
        print("Test call answered.")

        # Remember the owner before asking Asterisk to start playback.
        playback_channels[playback_id] = channel_id

        await asyncio.to_thread( # ensures answering completes before we request playback.
            send_ari_command,    # asyncio.to_thread: runs the blocking HTTP operation in a worker thread so it doesn’t block the entire asynchronous event loop.
            f"{channel_path}/play/{playback_id}",
            headers,
            {"media": "sound:hello-world,sound:silence/1"}, # Refers to an audio prompt on the PBX
        )
        print("Greeting playback requested.")

    except HTTPError as error:
        playback_channels.pop(playback_id, None) # Remove this playback if present; otherwise return None. That lets cleanup run without raising an error when the entry has already been removed.

        if error.code == 404:
            print("ARI resource not found; the caller may have hung up.")
        else:
            print(f"ARI command failed: HTTP {error.code}.")

    except (URLError, TimeoutError, OSError):
        playback_channels.pop(playback_id, None) # Remove this playback if present; otherwise return None. That lets cleanup run without raising an error when the entry has already been removed.
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

    # Tracks only the greeting playbacks created by this connection.
    playback_channels: dict[str, str] = {}

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
                await answer_and_greet(channel_id, headers, playback_channels)

            elif event_type == "PlaybackFinished":
                playback_id = event["playback"]["id"]
                # Remove before sending hangup. Once the completion event is handled, the same ID can’t trigger another hangup through this mapping.
                channel_id = playback_channels.pop(playback_id, None)

                # Only act on a playback that this controller tracked.
                if channel_id is not None:
                    print("Tracked greeting ended; requesting hangup.")
                    await hang_up(channel_id, headers)

            elif event_type == "StasisEnd":
                channel_id = event["channel"]["id"]

                # Collect matching entries before modifying the dictionary.
                finished_playbacks = [
                    playback_id
                    for playback_id, owner_channel_id
                    in playback_channels.items()
                    if owner_channel_id == channel_id
                ]

                # If the caller leaves early, any remaining greeting associations for that channel are removed.
                for playback_id in finished_playbacks:
                    playback_channels.pop(playback_id, None)

                print(
                    "Channel left the application. "
                    f"Tracked greetings remaining: {len(playback_channels)}"
                )

            elif event_type == "ApplicationReplaced":
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