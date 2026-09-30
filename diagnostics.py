"""Local config/build check by default. --database explicitly enables a read probe."""
import argparse
import asyncio
import sys
from config import load_settings
from kingcore.settings import ConfigError
from kingcore.database import DatabaseProbe

async def check(settings, database, catalog=False):
    from bot import create_application
    app = create_application(settings)
    groups = sorted(app.handlers)
    print(f"{settings.app_name}: configuração e composição de handlers OK; grupos={groups}")
    print("Telegram não conectado; tokens, acesso e permissões ainda não validados remotamente.")
    try:
        if catalog:
            from modules.catalog_client import CatalogError
            try:
                rows=await app.bot_data['catalog'].read(min(settings.admin_ids))
                print(f"Catálogo: API disponível; {len(rows)} animes visíveis ao administrador de teste.")
                return 0
            except CatalogError as exc:
                print(str(exc))
                return 1
        if database:
            result = await DatabaseProbe(settings).check()
            print(f"Supabase: {result.message}")
            return 0 if result.state == "reachable" else 1
        return 0
    finally:
        # Build creates HTTP clients but sends no requests; close both explicitly.
        for request in app.bot_data["runtime_requests"]:
            await request.shutdown()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", action="store_true", help="Faz SELECT sem retornar registros no Supabase")
    parser.add_argument("--catalog", action="store_true", help="Consulta API do Hub como administrador, somente leitura")
    args = parser.parse_args()
    try:
        return asyncio.run(check(load_settings(), args.database, args.catalog))
    except ConfigError as exc:
        print(f"Configuração: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
