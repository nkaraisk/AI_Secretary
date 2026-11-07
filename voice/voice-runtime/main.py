import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Environment variable: lets us change the Java service address without editing code.
def fetch_demo_configuration() -> dict:
    base_url = os.getenv(
        "TENANT_SERVICE_BASE_URL",
        "http://127.0.0.1:8081",
    ).rstrip("/")

# HTTP GET: requests information without creating or changing a booking.
    request = Request(
        url=f"{base_url}/api/v1/demo/tenant-configuration",
        headers={"Accept": "application/json"},
        method="GET",
    )

# Five-second timeout: prevents waiting indefinitely.
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def main() -> None:
    try:
        # JSON parsing: converts the response into Python data.
        configuration = fetch_demo_configuration()

        print("Connected to the tenant service.")
        print(json.dumps(configuration, indent=2, ensure_ascii=False))

    # Error handling: distinguishes a rejected request from a connectivity problem.
    except HTTPError as error:
        print(f"The tenant service returned HTTP {error.code}.")
        raise SystemExit(1) from error

    except (URLError, TimeoutError) as error:
        print(f"Could not reach the tenant service: {error}")
        raise SystemExit(1) from error

    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        print("The tenant service returned an invalid JSON response.")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()