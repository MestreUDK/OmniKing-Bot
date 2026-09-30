from kingcore import VERSION
from kingcore.security import is_private_admin

async def health(update, context):
    if update.effective_message:
        app_name = context.application.bot_data["settings"].app_name
        await update.effective_message.reply_text(f"✅ {app_name} {VERSION} ativo. Versão de testes.")

async def status(update, context):
    settings = context.application.bot_data["settings"]
    if not is_private_admin(update, settings):
        if update.effective_message:
            await update.effective_message.reply_text("Diagnóstico disponível somente ao administrador no privado.")
        return
    result = await context.application.bot_data["db"].check()
    await update.effective_message.reply_text(
        f"{settings.app_name} {VERSION}\nTelegram: conectado\nSupabase: {result.message}\n"
        "Etapa: fundação. Catálogo, player e gestão ainda não migrados."
    )
