from config import load_settings
from kingcore.logging_setup import configure_logging
from kingcore.runtime import build_base
from kingcore.settings import ConfigError
from register_handlers import register_handlers
from modules.catalog_client import CatalogConfig, CatalogClient
from kingcore.cache import TTLCache

def create_application(settings=None, *, request=None, updates_request=None, catalog_config=None, catalog_transport=None):
    settings = settings or load_settings()
    app = build_base(settings, request, updates_request)
    app.bot_data["catalog"] = CatalogClient(catalog_config or CatalogConfig.from_env(), catalog_transport, settings.force_ipv4)
    app.bot_data["catalog_sessions"] = TTLCache(ttl=600,maxsize=128)
    register_handlers(app)
    return app

def main():
    try:
        settings = load_settings()
        catalog_config = CatalogConfig.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuração: {exc}") from None
    configure_logging(settings)
    app = create_application(settings, catalog_config=catalog_config)
    app.run_polling(timeout=30, bootstrap_retries=3, drop_pending_updates=False)

if __name__ == "__main__":
    main()
