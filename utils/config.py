import os

# Global Telegram text limit
TELEGRAM_MAX_MSG = 4096


def get_token() -> str:
    """
    Read TELEGRAM_TOKEN from environment and fail fast if missing.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError(
            "You must define TELEGRAM_TOKEN with export before running the bot."
        )
    return token
