from config import load_settings
from kingcore.logging_setup import configure_logging
from kingcore.runtime import build_base
from kingcore.settings import ConfigError
from register_handlers import register_handlers

def create_application(settings=None, *, request=None, updates_request=None):
    settings = settings or load_settings()
    app = build_base(settings, request, updates_request)
    register_handlers(app)
    return app

def main():
    try:
        settings = load_settings()
    except ConfigError as exc:
        raise SystemExit(f"Configuração: {exc}") from None
    configure_logging(settings)
    app = create_application(settings)
    app.run_polling(timeout=30, bootstrap_retries=3, drop_pending_updates=False)

if __name__ == "__main__":
    main()
