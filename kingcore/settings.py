"""Configuration without I/O on import. No production defaults or embedded secrets."""
import base64
import json
import re
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urlsplit

class ConfigError(ValueError):
    pass

def privileged_key(key: str) -> bool:
    if key.startswith("sb_secret_"):
        return True
    try:
        part = key.split(".")[1]
        payload = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
        return isinstance(payload, dict) and payload.get("role") == "service_role"
    except (ValueError, IndexError, UnicodeDecodeError):
        return False

@dataclass(frozen=True)
class Settings:
    app_name: str
    bot_token: str = field(repr=False)
    admin_ids: frozenset[int]
    supabase_url: str = field(default="", repr=False)
    supabase_key: str = field(default="", repr=False)
    force_ipv4: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, app_name: str, env: Mapping[str, str]):
        if app_name not in {"OmniKing", "AdminKing"}:
            raise ConfigError("Aplicação desconhecida.")
        token = env.get("BOT_TOKEN", "").strip()
        if not re.fullmatch(r"[1-9][0-9]*:[A-Za-z0-9_-]{20,}", token):
            raise ConfigError("Preencha BOT_TOKEN com o token do bot de testes.")
        raw_ids = ",".join(filter(None, [env.get("ADMIN_IDS", ""), env.get("ADMIN_ID", "")]))
        ids = set()
        for item in raw_ids.split(","):
            item = item.strip()
            if not item:
                continue
            if not item.isascii() or not item.isdigit() or int(item) <= 0:
                raise ConfigError("ADMIN_IDS/ADMIN_ID deve conter IDs positivos, separados por vírgula.")
            ids.add(int(item))
        if not ids:
            raise ConfigError("Defina ADMIN_IDS ou ADMIN_ID para o diagnóstico privado.")
        url = env.get("SUPABASE_URL", "").strip().rstrip("/")
        key = env.get("SUPABASE_KEY", "").strip()
        if bool(url) != bool(key):
            raise ConfigError("Configure SUPABASE_URL e SUPABASE_KEY juntos, ou deixe ambos vazios.")
        if url:
            try:
                parts = urlsplit(url)
            except ValueError:
                raise ConfigError("SUPABASE_URL inválida.") from None
            if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
                    or parts.query or parts.fragment or parts.path):
                raise ConfigError("SUPABASE_URL deve ser a URL HTTPS do projeto, sem caminho ou credenciais.")
        if app_name == "OmniKing" and privileged_key(key):
            raise ConfigError("OmniKing não aceita chave service_role/sb_secret_. Use credencial restrita.")
        ipv4 = env.get("FORCE_IPV4", "true").strip().lower()
        if ipv4 not in {"true", "false"}:
            raise ConfigError("FORCE_IPV4 deve ser true ou false.")
        level = env.get("LOG_LEVEL", "INFO").strip().upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigError("LOG_LEVEL inválido.")
        return cls(app_name, token, frozenset(ids), url, key, ipv4 == "true", level)
