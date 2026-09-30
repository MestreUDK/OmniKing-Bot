"""A blocking pre-handler guard protects EVERY update in AdminKing."""
import logging
from telegram.ext import ApplicationHandlerStop

logger = logging.getLogger(__name__)

def is_private_admin(update, settings):
    user, chat = update.effective_user, update.effective_chat
    return bool(user and not user.is_bot and chat and chat.type == "private"
                and user.id == chat.id and user.id in settings.admin_ids)

async def admin_guard(update, context):
    if is_private_admin(update, context.application.bot_data["settings"]):
        return
    logger.warning("admin_access_denied update_id=%s", update.update_id)
    # Silent refusal avoids chat noise and denial-of-service amplification.
    # Includes messages, edited messages, callbacks, inline queries and posts.
    raise ApplicationHandlerStop
