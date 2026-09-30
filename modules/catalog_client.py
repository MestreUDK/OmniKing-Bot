"""Fresh authorization on every read. No actor snapshots are cached in the bot."""
import hashlib
import hmac
import os
import re
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit
import httpx
from kingcore.settings import ConfigError

PATH='/internal/omniking/catalog'

class CatalogError(Exception):
    pass

@dataclass(frozen=True)
class CatalogConfig:
    url: str=''
    secret: str=field(default='',repr=False)
    player_username: str='AnKPlayBot'

    @classmethod
    def from_env(cls,env=None):
        env=os.environ if env is None else env
        url=env.get('CATALOG_API_URL','').strip().rstrip('/')
        secret=env.get('OMNIKING_API_SECRET','').strip()
        player=env.get('LEGACY_PLAYER_USERNAME','AnKPlayBot').strip().lstrip('@')
        if bool(url)!=bool(secret):raise ConfigError('Configure CATALOG_API_URL e OMNIKING_API_SECRET juntos.')
        if secret and len(secret)<32:raise ConfigError('OMNIKING_API_SECRET precisa de pelo menos 32 caracteres.')
        if url:
            try:p=urlsplit(url)
            except ValueError:raise ConfigError('CATALOG_API_URL inválida.') from None
            local=p.scheme=='http' and p.hostname in {'127.0.0.1','localhost','::1'}
            if (p.scheme!='https' and not local) or not p.hostname or p.username or p.password or p.query or p.fragment or p.path:
                raise ConfigError('CATALOG_API_URL deve ser uma origem HTTPS; HTTP só em loopback para testes.')
            try:p.port
            except ValueError:raise ConfigError('Porta do catálogo inválida.') from None
        if not re.fullmatch(r'[A-Za-z0-9_]{5,32}',player):raise ConfigError('LEGACY_PLAYER_USERNAME inválido.')
        return cls(url,secret,player)

class CatalogClient:
    def __init__(self,config,transport=None,force_ipv4=True):
        self.config=config;self.transport=transport;self.force_ipv4=force_ipv4
    async def read(self,user_id):
        if not self.config.url:raise CatalogError('Catálogo não configurado. Peça ao administrador para concluir a integração com o Hub.')
        if type(user_id) is not int or not 0<user_id<10**19:raise CatalogError('Identidade Telegram inválida.')
        actor=str(user_id);stamp=str(int(time.time()))
        check=f'GET\n{PATH}\n{actor}\n{stamp}'
        signature=hmac.new(self.config.secret.encode(),check.encode(),hashlib.sha256).hexdigest()
        headers={'X-OmniKing-User':actor,'X-OmniKing-Time':stamp,'X-OmniKing-Signature':signature}
        try:
            # Separate short-lived client: safe across PTB diagnostics and polling lifecycles.
            transport=self.transport or httpx.AsyncHTTPTransport(local_address='0.0.0.0' if self.force_ipv4 else None)
            async with httpx.AsyncClient(transport=transport,timeout=httpx.Timeout(20,connect=5),follow_redirects=False) as client:
                async with client.stream('GET',self.config.url+PATH,headers=headers) as response:
                    if response.status_code==403:
                        raise CatalogError('Acesso indisponível. Confira sua conta e a inscrição no canal do acervo.')
                    if response.status_code!=200:raise CatalogError('Catálogo indisponível agora. Tente novamente em instantes.')
                    parts=[];size=0
                    async for chunk in response.aiter_bytes():
                        size+=len(chunk)
                        if size>32*1024*1024:raise CatalogError('Catálogo excedeu o limite de leitura desta versão.')
                        parts.append(chunk)
            import json
            data=json.loads(b''.join(parts))
            if not isinstance(data,dict) or data.get('contract')!=1 or not isinstance(data.get('animes'),list):raise ValueError
            rows=data['animes']
            if any(not isinstance(row,dict) or not isinstance(row.get('id'),str) for row in rows):raise ValueError
            return rows
        except CatalogError:raise
        except (httpx.HTTPError,ValueError,TypeError,UnicodeError):
            raise CatalogError('Catálogo indisponível agora. Tente novamente em instantes.') from None
