import logging
from uuid import uuid4
import httpx
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest
from kingcore import VERSION
from kingcore.cache import TTLCache
from kingcore.database import DatabaseProbe

logger = logging.getLogger(__name__)

async def post_init(application):
    settings = application.bot_data["settings"]
    logger.info("%s %s conectado como @%s", settings.app_name, VERSION, application.bot.username)

async def on_error(update, context):
    incident = uuid4().hex[:10]
    # No raw update, request, user message, secrets or exception body in logs.
    logger.error("incident=%s error_type=%s", incident, type(context.error).__name__)
    if update is not None and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"Não consegui concluir esta ação. Tente novamente. Referência: {incident}"
            )
        except TelegramError:
            pass

def build_base(settings, request=None, updates_request=None):
    def make_request(long_poll=False):
        kwargs = {}
        if settings.force_ipv4:
            kwargs["transport"] = httpx.AsyncHTTPTransport(local_address="0.0.0.0", retries=2)
        return HTTPXRequest(connect_timeout=15, read_timeout=40 if long_poll else 20,
                            write_timeout=20, pool_timeout=10, httpx_kwargs=kwargs)
    request = request if request is not None else make_request()
    updates_request = updates_request if updates_request is not None else make_request(True)
    app = (ApplicationBuilder().token(settings.bot_token)
           .request(request)
           .get_updates_request(updates_request)
           .concurrent_updates(False).post_init(post_init).build())
    app.bot_data.update(settings=settings, version=VERSION, cache=TTLCache(), db=DatabaseProbe(settings))
    app.bot_data["runtime_requests"] = (request, updates_request)
    app.add_error_handler(on_error)
    return app
