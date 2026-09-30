"""Pure parser only. No DB lookups, permission checks or content delivery here."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class LinkTarget:
    kind: str
    value: str = ""
    season_id: int | None = None
    episode_number: int | None = None
    legacy: bool = False

def normalize_anime_id(value):
    match = re.fullmatch(r"([A-Za-z]\d{2})-?(\d{4,5})", value)
    return f"{match[1].upper()}-{match[2]}" if match else value

def parse_payload(payload: str) -> LinkTarget:
    if not payload:
        return LinkTarget("home")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", payload):
        raise ValueError("Payload inválido")
    if payload.startswith("anime_"):
        value = payload[6:]
        if not value:
            raise ValueError("Anime ausente")
        return LinkTarget("anime", normalize_anime_id(value))
    if payload.startswith("saga_"):
        if not payload[5:]:
            raise ValueError("Saga ausente")
        return LinkTarget("saga", payload[5:])
    if payload.startswith("ep_"):
        try:
            anime, season, episode = payload[3:].rsplit("_", 2)
            if not anime or not season.isdigit() or not episode.isdigit() or int(season) < 1:
                raise ValueError
            return LinkTarget("episode", normalize_anime_id(anime), int(season), int(episode))
        except ValueError:
            raise ValueError("Episódio inválido") from None
    if payload.startswith("get_"):
        value = payload[4:]
        if not value.isdigit() or int(value) < 1:
            raise ValueError("ID de episódio inválido")
        return LinkTarget("episode_id", str(int(value)), legacy=True)
    for prefix in ("busca_", "buscar_"):
        if payload.startswith(prefix):
            value = payload[len(prefix):].replace("_", " ").strip()
            if not value:
                raise ValueError("Busca vazia")
            return LinkTarget("search", value, legacy=prefix == "buscar_")
    if payload.startswith("atalhos_"):
        letter = payload[8:].upper()
        if letter not in tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ("NUM", "PROIBIDOS"):
            raise ValueError("Atalho inválido")
        return LinkTarget("shortcut", letter)
    if payload in {"feedback", "feedback_reportar", "feedback_sugestao"}:
        return LinkTarget("feedback", payload, legacy=True)
    if re.fullmatch(r"[A-Za-z]\d{2}-?\d{4,5}", payload):
        return LinkTarget("anime", normalize_anime_id(payload), legacy=True)
    # Legacy AnK Play tries an exact anime ID first, then the saga slug.
    # The future resolver must retain this precedence, including custom IDs.
    return LinkTarget("legacy_lookup", payload, legacy=True)
