from modules.deeplinks import parse_payload

async def start(update, context):
    if not update.effective_message:
        return
    if context.args:
        try:
            parse_payload(" ".join(context.args))
        except ValueError:
            await update.effective_message.reply_text("Link inválido. Use /start para abrir o menu.")
            return
        await update.effective_message.reply_text(
            "Este link será atendido quando a migração do catálogo/player estiver disponível. "
            "Esta versão ainda é uma fundação de testes."
        )
        return
    await update.effective_message.reply_text(
        "👑 OmniKing | Versão de testes\n\n"
        "A nova casa do catálogo e do player AniKing está em construção.\n"
        "Nesta etapa você pode testar /health e consultar /ajuda."
    )

async def help_command(update, context):
    if update.effective_message:
        await update.effective_message.reply_text(
            "/start - Início\n/health - Verificar se o bot está ativo\n"
            "/status - Diagnóstico privado do administrador\n\n"
            "Catálogo, favoritos, perfil e reprodução ainda serão migrados."
        )
