"""Foundation probe only: no user registration, writes or schema migration."""
import asyncio
from dataclasses import dataclass
from threading import Lock

@dataclass(frozen=True)
class DatabaseStatus:
    state: str
    message: str

class DatabaseProbe:
    def __init__(self, settings, client_factory=None):
        self.settings = settings
        self._client = None
        self._factory = client_factory
        self._lock = Lock()

    def _check(self):
        if not self.settings.supabase_url:
            return DatabaseStatus("unconfigured", "não configurado (permitido nesta etapa)")
        with self._lock:
            try:
                if self._client is None:
                    if self._factory is None:
                        from supabase import create_client, ClientOptions
                        self._client = create_client(
                            self.settings.supabase_url, self.settings.supabase_key,
                            options=ClientOptions(postgrest_client_timeout=10),
                        )
                    else:
                        self._client = self._factory(self.settings.supabase_url, self.settings.supabase_key)
                self._client.table("animes").select("id").limit(0).execute()
                return DatabaseStatus("reachable", "API respondeu; dados e políticas RLS ainda não validados")
            except Exception:
                # SDK exceptions can contain URLs, credentials or table data.
                return DatabaseStatus("unavailable", "falha na consulta; confira configuração, rede e permissões")

    async def check(self):
        return await asyncio.to_thread(self._check)
