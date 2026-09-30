import logging
import re

class SafeFormatter(logging.Formatter):
    def __init__(self, secrets=()):
        super().__init__("%(asctime)s %(levelname)s %(name)s %(message)s")
        self.secrets = tuple(value for value in secrets if value)

    def format(self, record):
        text = super().format(record)
        for secret in self.secrets:
            text = text.replace(secret, "[REDACTED]")
        text = re.sub(r"\b\d{7,12}:[A-Za-z0-9_-]{20,}\b", "[REDACTED_TOKEN]", text)
        text = re.sub(r"eyJ[A-Za-z0-9_.-]{50,}", "[REDACTED_JWT]", text)
        return text

def configure_logging(settings):
    handler = logging.StreamHandler()
    handler.setFormatter(SafeFormatter((settings.bot_token, settings.supabase_key)))
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)
    for name in ("httpx", "httpcore", "telegram", "supabase", "postgrest"):
        logging.getLogger(name).setLevel(logging.WARNING)
