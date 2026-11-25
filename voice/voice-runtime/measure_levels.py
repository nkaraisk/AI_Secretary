import asyncio
import json
from math import isqrt

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed


def ulaw_magnitude(code: int) -> int: # Converts an encoded byte into a signal magnitude.
    value = (~code) & 0x7F
    exponent = value >> 4
    mantissa = value & 0x0F
    return (((mantissa << 3) + 132) << exponent) - 132


POWER = tuple(ulaw_magnitude(code) ** 2 for code in range(256)) # Calculates all 256 possible squared values once, so each incoming sample needs only a lookup.


async def measure_call(connection) -> None:
    levels = []
    skipped = 0
    ready = False

    try:
        async for message in connection:
            if isinstance(message, str):
                event = json.loads(message)
                if event.get("event") == "MEDIA_START": # MEDIA_START checks the assumption behind your timing detector.
                    codec = event.get("format")
                    size = event.get("optimal_frame_size")
                    print(f"Media started: codec={codec}, frame_bytes={size}")
                    ready = codec == "ulaw" and size == 160
                continue

            if not ready or len(message) != 160:
                skipped += 1
                continue

            mean_square = sum(POWER[byte] for byte in message) // len(message)
            levels.append(isqrt(mean_square))

    except ConnectionClosed:
        print("Media connection closed.")
    finally:
        print(f"Frames measured={len(levels)}, skipped={skipped}")
        if levels:
            levels.sort()
            last = len(levels) - 1
            print(f"RMS p50={levels[last // 2]}, p95={levels[last * 95 // 100]}") # RMS gives one level per frame. The meter averages the squared sample magnitudes and takes the square root.
                                                                                  # A larger result means more signal energy. A loud keyboard tap can also produce a large result,
                                                                                  # which is one reason our detector requires consecutive active frames. p50 and p95 summarize the call. p50 is the middle frame level.
                                                                                  # p95 is near the louder end. We care especially about quiet-call p95 versus speaking-call p50.

async def main() -> None:
    server = await serve(
        measure_call,
        "127.0.0.1",
        18765,
        subprotocols=["media"],
        compression=None,
    )
    print("Level meter listening on 127.0.0.1:18765")
    await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Level meter stopped.")