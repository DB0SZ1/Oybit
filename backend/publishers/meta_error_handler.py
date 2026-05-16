import httpx
from backend.utils.exceptions import (
    MetaTokenExpiredError, MetaRateLimitError, MetaInvalidParamError,
    MetaBlockedError, MetaAPIError
)

def check_meta_response(response: httpx.Response, context: str) -> dict:
    data = response.json()
    if "error" in data:
        error = data["error"]
        code = error.get("code")
        message = error.get("message", "Unknown Meta error")

        if code == 190:  # Token expired/invalid
            raise MetaTokenExpiredError(f"Token expired for {context}: {message}")
        elif code == 100:  # Invalid parameter
            raise MetaInvalidParamError(f"Invalid param in {context}: {message}")
        elif code in [17, 32]:  # Rate limit
            raise MetaRateLimitError(f"Rate limited in {context}: {message}")
        elif code == 368:  # Temporarily blocked
            raise MetaBlockedError(f"Account temporarily blocked: {message}")
        else:
            raise MetaAPIError(f"Meta error {code} in {context}: {message}")

    return data
